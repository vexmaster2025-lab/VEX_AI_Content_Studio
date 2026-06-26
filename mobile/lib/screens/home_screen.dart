import 'package:flutter/material.dart';

import '../services/auth_service.dart';
import '../services/billing_service.dart';
import '../services/content_service.dart';
import 'login_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _titleController = TextEditingController();
  final _bodyController = TextEditingController();
  String _status = 'draft';
  bool _isLoading = true;
  String? _error;
  AuthUser? _user;
  BillingStatus? _billing;
  List<ContentItem> _items = const [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _titleController.dispose();
    _bodyController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final results = await Future.wait<dynamic>([
        AuthService.me(),
        BillingService.status(),
        ContentService.list(),
      ]);
      if (!mounted) return;
      setState(() {
        _user = results[0] as AuthUser;
        _billing = results[1] as BillingStatus;
        _items = results[2] as List<ContentItem>;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (!mounted) return;
      setState(() => _isLoading = false);
    }
  }

  Future<void> _createContent() async {
    if (_titleController.text.trim().length < 3 || _bodyController.text.trim().length < 10) {
      setState(
        () => _error = 'Title must be 3+ characters and body must be 10+ characters',
      );
      return;
    }
    try {
      await ContentService.create(
        _titleController.text.trim(),
        _bodyController.text.trim(),
        _status,
      );
      if (!mounted) return;
      _titleController.clear();
      _bodyController.clear();
      await _load();
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString().replaceFirst('Exception: ', ''));
    }
  }

  Future<void> _logout() async {
    await AuthService.logout();
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('VEX Content Studio'),
        actions: [
          IconButton(
            onPressed: _load,
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
          ),
          IconButton(
            onPressed: _logout,
            icon: const Icon(Icons.logout),
            tooltip: 'Sign out',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (_error != null) ...[
                    Text(
                      _error!,
                      style: TextStyle(color: Theme.of(context).colorScheme.error),
                    ),
                    const SizedBox(height: 16),
                  ],
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _user?.email ?? '',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 8),
                          Text('Plan: ${_billing?.plan ?? 'free'}'),
                          Text('Status: ${_billing?.subscriptionStatus ?? 'inactive'}'),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            'New content',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            controller: _titleController,
                            decoration: const InputDecoration(labelText: 'Title'),
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            controller: _bodyController,
                            decoration: const InputDecoration(labelText: 'Body'),
                            minLines: 3,
                            maxLines: 6,
                          ),
                          const SizedBox(height: 12),
                          DropdownButtonFormField<String>(
                            value: _status,
                            items: const [
                              DropdownMenuItem(value: 'draft', child: Text('Draft')),
                              DropdownMenuItem(value: 'published', child: Text('Published')),
                            ],
                            onChanged: (value) =>
                                setState(() => _status = value ?? 'draft'),
                            decoration: const InputDecoration(labelText: 'Status'),
                          ),
                          const SizedBox(height: 16),
                          FilledButton(
                            onPressed: _createContent,
                            child: const Text('Save content'),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text('Content', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 8),
                  if (_items.isEmpty)
                    const Text('No content items yet.')
                  else
                    ..._items.map(
                      (item) => Card(
                        child: ListTile(
                          title: Text(item.title),
                          subtitle: Text('${item.status}\n${item.body}'),
                          isThreeLine: true,
                          trailing: PopupMenuButton<String>(
                            onSelected: (value) async {
                              if (value == 'toggle') {
                                await ContentService.toggleStatus(item);
                              } else if (value == 'delete') {
                                await ContentService.delete(item);
                              }
                              await _load();
                            },
                            itemBuilder: (context) => [
                              PopupMenuItem(
                                value: 'toggle',
                                child: Text(item.status == 'draft' ? 'Publish' : 'Unpublish'),
                              ),
                              const PopupMenuItem(value: 'delete', child: Text('Delete')),
                            ],
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
    );
  }
}
