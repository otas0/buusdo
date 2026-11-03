import 'dart:convert';

import 'package:http/http.dart' as http;

/// Thin client for companion protocol v1 (LAN only).
class CompanionApi {
  CompanionApi({required this.baseUrl, this.token});

  String baseUrl;
  String? token;

  Uri _u(String path) => Uri.parse('${baseUrl.replaceAll(RegExp(r'/$'), '')}$path');

  Future<Map<String, dynamic>> health() async {
    final resp = await http.get(_u('/v1/health')).timeout(const Duration(seconds: 5));
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> pair({required String code, String label = 'mobile'}) async {
    final resp = await http
        .post(
          _u('/v1/pair'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'code': code, 'label': label}),
        )
        .timeout(const Duration(seconds: 8));
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (resp.statusCode != 200 || body['ok'] != true) {
      throw Exception(body['error']?.toString() ?? 'pair failed (${resp.statusCode})');
    }
    token = body['token']?.toString();
    return body;
  }

  Future<Map<String, dynamic>> rpc(String op, {Map<String, dynamic>? params}) async {
    final t = token;
    if (t == null || t.isEmpty) {
      throw Exception('not paired');
    }
    final resp = await http
        .post(
          _u('/v1/rpc'),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $t',
          },
          body: jsonEncode({
            'protocol_version': 1,
            'op': op,
            'params': params ?? <String, dynamic>{},
          }),
        )
        .timeout(const Duration(seconds: 8));
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    if (body['ok'] != true) {
      throw Exception(body['error']?.toString() ?? 'rpc failed');
    }
    return (body['data'] as Map<String, dynamic>?) ?? <String, dynamic>{};
  }
}
