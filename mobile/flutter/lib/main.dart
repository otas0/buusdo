import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  runApp(BuusdoCompanionApp(prefs: prefs));
}

class BuusdoCompanionApp extends StatelessWidget {
  const BuusdoCompanionApp({super.key, required this.prefs});

  final SharedPreferences prefs;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'buusdo companion',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFE85D04),
          brightness: Brightness.light,
          surface: const Color(0xFFE8EAED),
        ),
        useMaterial3: true,
      ),
      home: CompanionHome(prefs: prefs),
    );
  }
}

class CompanionHome extends StatefulWidget {
  const CompanionHome({super.key, required this.prefs});

  final SharedPreferences prefs;

  @override
  State<CompanionHome> createState() => _CompanionHomeState();
}

class _CompanionHomeState extends State<CompanionHome> {
  late final TextEditingController _urlCtrl;
  late final TextEditingController _codeCtrl;
  late CompanionApi _api;

  String? _error;
  bool _busy = false;
  Map<String, dynamic>? _status;
  List<String> _recent = const [];

  static const _kUrl = 'companion_base_url';
  static const _kToken = 'companion_token';

  @override
  void initState() {
    super.initState();
    final url = widget.prefs.getString(_kUrl) ?? 'http://127.0.0.1:8765';
    final token = widget.prefs.getString(_kToken);
    _urlCtrl = TextEditingController(text: url);
    _codeCtrl = TextEditingController();
    _api = CompanionApi(baseUrl: url, token: token);
    if (token != null && token.isNotEmpty) {
      _refreshStatus();
    }
  }

  @override
  void dispose() {
    _urlCtrl.dispose();
    _codeCtrl.dispose();
    super.dispose();
  }

  Future<void> _persist() async {
    await widget.prefs.setString(_kUrl, _api.baseUrl);
    final t = _api.token;
    if (t != null) {
      await widget.prefs.setString(_kToken, t);
    } else {
      await widget.prefs.remove(_kToken);
    }
  }

  Future<void> _run(Future<void> Function() fn) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await fn();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pair() async {
    await _run(() async {
      _api.baseUrl = _urlCtrl.text.trim();
      await _api.pair(code: _codeCtrl.text.trim());
      await _persist();
      await _loadStatus();
    });
  }

  Future<void> _refreshStatus() async {
    await _run(() async {
      _api.baseUrl = _urlCtrl.text.trim();
      await _loadStatus();
    });
  }

  Future<void> _loadStatus() async {
    final data = await _api.rpc('status');
    final recent = (data['recent_game_names'] as List<dynamic>? ?? const [])
        .map((e) => e.toString())
        .where((e) => e.isNotEmpty)
        .toList();
    setState(() {
      _status = data;
      _recent = recent;
    });
  }

  Future<void> _requestScan() async {
    await _run(() async {
      await _api.rpc('request_scan');
      await _loadStatus();
    });
  }

  Future<void> _unpairLocal() async {
    await _run(() async {
      _api.token = null;
      await _persist();
      setState(() {
        _status = null;
        _recent = const [];
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final tablet = width >= 700;

    final pairPane = _PairPane(
      urlCtrl: _urlCtrl,
      codeCtrl: _codeCtrl,
      busy: _busy,
      paired: _api.token != null && _api.token!.isNotEmpty,
      error: _error,
      onPair: _pair,
      onRefresh: _refreshStatus,
      onScan: _requestScan,
      onUnpair: _unpairLocal,
      status: _status,
    );

    final recentPane = _RecentPane(recent: _recent);

    if (tablet) {
      return Scaffold(
        appBar: AppBar(title: const Text('buusdo companion')),
        body: Row(
          children: [
            Expanded(flex: 3, child: pairPane),
            const VerticalDivider(width: 1),
            Expanded(flex: 2, child: recentPane),
          ],
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('buusdo companion')),
      body: ListView(
        children: [
          pairPane,
          const Divider(height: 1),
          SizedBox(height: 220, child: recentPane),
        ],
      ),
    );
  }
}

class _PairPane extends StatelessWidget {
  const _PairPane({
    required this.urlCtrl,
    required this.codeCtrl,
    required this.busy,
    required this.paired,
    required this.error,
    required this.onPair,
    required this.onRefresh,
    required this.onScan,
    required this.onUnpair,
    required this.status,
  });

  final TextEditingController urlCtrl;
  final TextEditingController codeCtrl;
  final bool busy;
  final bool paired;
  final String? error;
  final VoidCallback onPair;
  final VoidCallback onRefresh;
  final VoidCallback onScan;
  final VoidCallback onUnpair;
  final Map<String, dynamic>? status;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'Companion only — no remote install or inject. Pair from the desktop Companion dialog.',
          style: TextStyle(fontSize: 13),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: urlCtrl,
          decoration: const InputDecoration(
            labelText: 'LAN URL',
            hintText: 'http://192.168.x.x:8765',
            border: OutlineInputBorder(),
          ),
          enabled: !busy,
        ),
        const SizedBox(height: 8),
        TextField(
          controller: codeCtrl,
          decoration: const InputDecoration(
            labelText: 'Pairing code',
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.number,
          enabled: !busy,
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            FilledButton(onPressed: busy ? null : onPair, child: const Text('Pair')),
            OutlinedButton(onPressed: busy || !paired ? null : onRefresh, child: const Text('Status')),
            FilledButton.tonal(
              onPressed: busy || !paired ? null : onScan,
              child: const Text('Request scan'),
            ),
            TextButton(onPressed: busy || !paired ? null : onUnpair, child: const Text('Forget token')),
          ],
        ),
        if (error != null) ...[
          const SizedBox(height: 12),
          Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
        ],
        if (status != null) ...[
          const SizedBox(height: 16),
          Text('Host: ${status!['host_label'] ?? '—'}', style: const TextStyle(fontWeight: FontWeight.w600)),
          Text('App: ${status!['app_version'] ?? '—'}'),
          Text('Paired: ${status!['paired'] == true}'),
          if (status!['last_history_summary'] != null && '${status!['last_history_summary']}'.isNotEmpty)
            Text('History: ${status!['last_history_summary']}'),
          const SizedBox(height: 8),
          ...(status!['notes'] as List<dynamic>? ?? const []).map((n) => Text('• $n')),
        ],
        if (busy) ...[
          const SizedBox(height: 16),
          const LinearProgressIndicator(),
        ],
      ],
    );
  }
}

class _RecentPane extends StatelessWidget {
  const _RecentPane({required this.recent});

  final List<String> recent;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Text('Recent games', style: TextStyle(fontWeight: FontWeight.w600)),
        ),
        Expanded(
          child: recent.isEmpty
              ? const Center(child: Text('No recent games yet'))
              : ListView.separated(
                  itemCount: recent.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, i) => ListTile(title: Text(recent[i])),
                ),
        ),
      ],
    );
  }
}
