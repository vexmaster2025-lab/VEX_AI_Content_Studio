import 'dart:convert';

import 'package:http/http.dart' as http;

import 'auth_service.dart';

class ContentItem {
  const ContentItem({
    required this.id,
    required this.title,
    required this.body,
    required this.status,
  });

  final int id;
  final String title;
  final String body;
  final String status;

  factory ContentItem.fromJson(Map<String, dynamic> json) {
    return ContentItem(
      id: json['id'] as int,
      title: json['title'] as String,
      body: json['body'] as String,
      status: json['status'] as String,
    );
  }
}

class ContentService {
  static Future<List<ContentItem>> list() async {
    final response = await http.get(
      Uri.parse('${AuthService.apiUrl}/content'),
      headers: await AuthService.authHeaders(),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as List<dynamic>;
      return data.map((item) => ContentItem.fromJson(item as Map<String, dynamic>)).toList();
    }
    throw Exception('Unable to load content');
  }

  static Future<void> create(String title, String body, String status) async {
    final response = await http.post(
      Uri.parse('${AuthService.apiUrl}/content'),
      headers: await AuthService.authHeaders(),
      body: jsonEncode({'title': title, 'body': body, 'status': status}),
    );
    if (response.statusCode != 201) {
      throw Exception('Unable to create content');
    }
  }

  static Future<void> toggleStatus(ContentItem item) async {
    final nextStatus = item.status == 'draft' ? 'published' : 'draft';
    final response = await http.patch(
      Uri.parse('${AuthService.apiUrl}/content/${item.id}'),
      headers: await AuthService.authHeaders(),
      body: jsonEncode({'status': nextStatus}),
    );
    if (response.statusCode != 200) {
      throw Exception('Unable to update content');
    }
  }

  static Future<void> delete(ContentItem item) async {
    final response = await http.delete(
      Uri.parse('${AuthService.apiUrl}/content/${item.id}'),
      headers: await AuthService.authHeaders(),
    );
    if (response.statusCode != 204) {
      throw Exception('Unable to delete content');
    }
  }
}
