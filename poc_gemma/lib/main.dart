import 'package:flutter/material.dart';
import 'package:flutter_gemma/flutter_gemma.dart';
import 'package:flutter_gemma_mediapipe/flutter_gemma_mediapipe.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await FlutterGemma.initialize(
      inferenceEngines: [
        MediaPipeEngine(),
      ],
    );
  } catch (e) {
    debugPrint('Gemma initialization error: $e');
  }
  runApp(const GemmaPocApp());
}

class GemmaPocApp extends StatelessWidget {
  const GemmaPocApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Gemma On-Device POC',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const GemmaPocScreen(),
    );
  }
}

class GemmaPocScreen extends StatefulWidget {
  const GemmaPocScreen({super.key});

  @override
  State<GemmaPocScreen> createState() => _GemmaPocScreenState();
}

class _GemmaPocScreenState extends State<GemmaPocScreen> {
  final TextEditingController _promptController = TextEditingController();
  String _response = 'Awaiting model input...';
  bool _isLoading = false;
  String _statusMessage = 'Initializing engine...';
  List<String> _installedModels = [];

  @override
  void initState() {
    super.initState();
    _checkModelStatus();
  }

  Future<void> _checkModelStatus() async {
    setState(() {
      _statusMessage = 'Checking for local Gemma weights on device storage...';
    });
    try {
      final models = await FlutterGemma.listInstalledModels();
      setState(() {
        _installedModels = models;
        _statusMessage = models.isNotEmpty
            ? 'Model available: ${models.join(", ")}'
            : 'No local Gemma weights found on device storage.';
      });
    } catch (e) {
      setState(() {
        _statusMessage = 'Status check failed: $e';
      });
    }
  }

  Future<void> _sendPrompt() async {
    final prompt = _promptController.text.trim();
    if (prompt.isEmpty) return;

    setState(() {
      _isLoading = true;
      _response = 'Generating on-device...';
    });

    try {
      final model = await FlutterGemma.getActiveModel(maxTokens: 512);
      final session = await model.createSession();
      await session.addQueryChunk(Message.text(text: prompt, isUser: true));
      final output = await session.getResponse();

      setState(() {
        _response = output;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _response = 'Inference error: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('On-Device Gemma POC'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              color: _installedModels.isNotEmpty
                  ? Colors.green.shade50
                  : Colors.amber.shade50,
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Text(
                  'Runtime Status: $_statusMessage',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _promptController,
              decoration: const InputDecoration(
                labelText: 'Enter prompt for Gemma',
                border: OutlineInputBorder(),
                hintText: 'e.g. What is Section 139 of the Companies Act?',
              ),
              maxLines: 3,
            ),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _sendPrompt,
              icon: _isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.send),
              label: Text(_isLoading ? 'Inferencing...' : 'Send Prompt to Gemma'),
            ),
            const SizedBox(height: 16),
            const Text(
              'Gemma Response:',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(12.0),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade400),
                  borderRadius: BorderRadius.circular(8.0),
                  color: Colors.grey.shade50,
                ),
                child: SingleChildScrollView(
                  child: Text(
                    _response,
                    style: const TextStyle(fontSize: 15, height: 1.4),
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
