import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class AuthUser {
  const AuthUser({
    required this.email,
    required this.plan,
    required this.subscriptionStatus,
    required this.hasActiveSubscription,
  });

  final String email;
  final String plan;
  final String subscriptionStatus;
  final bool hasActiveSubscription;

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      email: json['email'] as String,
      plan: json['plan'] as String,
      subscriptionStatus: json['subscription_status'] as String,
      hasActiveSubscription: json['has_active_subscription'] as bool,
    );
  }
}

class AuthService {
  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'vex_token';
  static const apiUrl = String.fromEnvironment('API_URL', defaultValue: 'http://localhost:8000/api/v1');

  static Future<bool> isAuthenticated() async {
    final token = await _storage.read(key: _tokenKey);
    return token != null && token.isNotEmpty;
  }

  static Future<String?> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$apiUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await _storage.write(key: _tokenKey, value: data['access_token']);
      return null;
    }
    return jsonDecode(response.body)['detail'] ?? 'Login failed';
  }

  static Future<String?> register(String email, String password, String? fullName) async {
    final response = await http.post(
      Uri.parse('$apiUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password, 'full_name': fullName}),
    );

    if (response.statusCode == 201) {
      return await login(email, password);
    }
    return _errorMessage(response, 'Registration failed');
  }

  static Future<AuthUser> me() async {
    final response = await http.get(
      Uri.parse('$apiUrl/auth/me'),
      headers: await authHeaders(),
    );
    if (response.statusCode == 200) {
      return AuthUser.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw Exception(_errorMessage(response, 'Unable to load profile'));
  }

  static Future<void> logout() async {
    await _storage.delete(key: _tokenKey);
  }

  static Future<String?> token() async => await _storage.read(key: _tokenKey);

  static Future<Map<String, String>> authHeaders() async {
    final value = await token();
    return {
      'Content-Type': 'application/json',
      if (value != null) 'Authorization': 'Bearer $value',
    };
  }

  static String _errorMessage(http.Response response, String fallback) {
    try {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      return data['detail'] as String? ?? fallback;
    } catch (_) {
      return fallback;
    }
  }
}
