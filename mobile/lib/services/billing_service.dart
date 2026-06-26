import 'dart:convert';

import 'package:http/http.dart' as http;

import 'auth_service.dart';

class BillingStatus {
  const BillingStatus({
    required this.plan,
    required this.subscriptionStatus,
    required this.hasActiveSubscription,
  });

  final String plan;
  final String subscriptionStatus;
  final bool hasActiveSubscription;

  factory BillingStatus.fromJson(Map<String, dynamic> json) {
    return BillingStatus(
      plan: json['plan'] as String,
      subscriptionStatus: json['subscription_status'] as String,
      hasActiveSubscription: json['has_active_subscription'] as bool,
    );
  }
}

class BillingService {
  static Future<BillingStatus> status() async {
    final response = await http.get(
      Uri.parse('${AuthService.apiUrl}/billing/status'),
      headers: await AuthService.authHeaders(),
    );
    if (response.statusCode == 200) {
      return BillingStatus.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw Exception('Unable to load billing status');
  }
}
