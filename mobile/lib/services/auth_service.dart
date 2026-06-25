import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class AuthService {
  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'vex_token';
  static const _apiUrl = String.fromEnvironment('API_URL', defaultValue: 'http://localhost:8000');

  static Future<bool> isAuthenticated() async {
    final token = await _storage.read(key: _tokenKey);
    return token != null && token.isNotEmpty;
  }

  static Future<String?> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$_apiUrl/login'),
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

  static Future<void> logout() async {
    await _storage.delete(key: _tokenKey);
  }

  static Future<String?> token() async => await _storage.read(key: _tokenKey);
}
