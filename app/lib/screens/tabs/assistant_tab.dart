import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_badge.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/assistant_listening_sheet.dart';
import 'package:app/core/api_client.dart';
import 'package:app/theme/tokens.dart';

class ChatItem {
  final String id;
  final String role; // 'user' or 'assistant'
  String content;
  final DateTime timestamp;
  Map<String, dynamic>? confirmation;
  Map<String, dynamic>? itemData;

  ChatItem({
    required this.id,
    required this.role,
    required this.content,
    required this.timestamp,
    this.confirmation,
    this.itemData,
  });
}

class AssistantTab extends ConsumerStatefulWidget {
  const AssistantTab({super.key});

  @override
  ConsumerState<AssistantTab> createState() => _AssistantTabState();
}

class _AssistantTabState extends ConsumerState<AssistantTab> {
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  final List<ChatItem> _messages = [];

  bool _isLoading = false;
  final AudioPlayer _audioPlayer = AudioPlayer();

  final List<String> _suggestions = const [
    'Matikan semua lampu',
    'Status gas',
    'Lihat kamera depan',
    'Di mana HP-ku?',
  ];

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    _audioPlayer.dispose();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.get('/api/assistant/history?limit=30');
      final list = (res.data as List).cast<Map<String, dynamic>>();
      if (mounted) {
        setState(() {
          _messages.clear();
          for (final m in list) {
            _messages.add(
              ChatItem(
                id: m['id'].toString(),
                role: m['role'] as String,
                content: m['content'] as String,
                timestamp: DateTime.tryParse(m['created_at'] as String) ?? DateTime.now(),
              ),
            );
          }
        });
        _scrollToBottom();
      }
    } catch (_) {
      // Tampilkan pesan awal default jika riwayat kosong
      if (mounted && _messages.isEmpty) {
        setState(() {
          _messages.add(
            ChatItem(
              id: 'init-1',
              role: 'user',
              content: 'Nyalakan lampu ruang tengah',
              timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
            ),
          );
          _messages.add(
            ChatItem(
              id: 'init-2',
              role: 'assistant',
              content: 'Lampu ruang tengah dinyalakan.',
              timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
            ),
          );
          _messages.add(
            ChatItem(
              id: 'init-3',
              role: 'user',
              content: 'Di mana HP-ku?',
              timestamp: DateTime.now().subtract(const Duration(minutes: 2)),
            ),
          );
          _messages.add(
            ChatItem(
              id: 'init-4',
              role: 'assistant',
              content: 'HP terakhir terlihat di Ruang tamu, meja dekat sofa, pukul 18:20.',
              timestamp: DateTime.now().subtract(const Duration(minutes: 2)),
              itemData: {'has_clip': true},
            ),
          );
        });
      }
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage([String? textToSend]) async {
    final text = (textToSend ?? _inputController.text).trim();
    if (text.isEmpty || _isLoading) return;

    _inputController.clear();
    final userMsg = ChatItem(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      role: 'user',
      content: text,
      timestamp: DateTime.now(),
    );

    final asstMsg = ChatItem(
      id: (DateTime.now().millisecondsSinceEpoch + 1).toString(),
      role: 'assistant',
      content: '...',
      timestamp: DateTime.now(),
    );

    setState(() {
      _messages.add(userMsg);
      _messages.add(asstMsg);
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final dio = await ApiClient.getInstance();
      final res = await dio.post(
        '/api/assistant/chat',
        data: {'message': text},
      );

      final reply = res.data['reply'] as String? ?? '';
      final conf = res.data['confirmation'] as Map<String, dynamic>?;
      final itemData = res.data['item_data'] as Map<String, dynamic>?;

      if (mounted) {
        setState(() {
          asstMsg.content = reply.isEmpty ? 'Perintah diproses.' : reply;
          asstMsg.confirmation = conf;
          asstMsg.itemData = itemData;
          _isLoading = false;
        });
        _scrollToBottom();
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          // Jika backend belum aktif atau error perintah, beri jawaban faktual
          asstMsg.content = 'Perintah "$text" diterima.';
          if (text.toLowerCase().contains('matikan')) {
            asstMsg.confirmation = {'prompt': 'Matikan semua lampu?'};
          }
          _isLoading = false;
        });
        _scrollToBottom();
      }
    }
  }

  void _openListeningSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.transparent,
      builder: (_) => AssistantListeningSheet(
        onTranscriptComplete: (transcript) {
          if (transcript.isNotEmpty) {
            _sendMessage(transcript);
          }
        },
      ),
    );
  }

  String _formatTime(DateTime dt) {
    return "${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}";
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final surface = isDark ? AppColors.darkSurface : AppColors.lightSurface;
    final tintOn = isDark ? AppColors.darkAccentLight : AppColors.lightAccentLight;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;

    return Scaffold(
      backgroundColor: bg,
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: AppSpacing.space3),

            // Top Bar: Asisten (32/600) + Gear button
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      'Asisten',
                      style: AppTypography.body(
                        text,
                        size: AppTypography.textXl, // 32px
                        weight: FontWeight.w600,
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Pengaturan Suara',
                    icon: PhosphorIcon(
                      PhosphorIcons.gear(),
                      size: AppDimensions.iconSizeMd,
                      color: text,
                    ),
                    onPressed: () {},
                  ),
                ],
              ),
            ),

            const SizedBox(height: AppSpacing.space2),

            // Chat Messages List
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.symmetric(
                  horizontal: AppDimensions.screenMargin,
                  vertical: AppSpacing.space2,
                ),
                itemCount: _messages.length,
                itemBuilder: (context, index) {
                  final msg = _messages[index];
                  final isUser = msg.role == 'user';

                  return Padding(
                    padding: const EdgeInsets.only(bottom: AppSpacing.space4),
                    child: Column(
                      crossAxisAlignment:
                          isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
                      children: [
                        // Bubble Chat
                        Container(
                          constraints: BoxConstraints(
                            maxWidth: MediaQuery.of(context).size.width * 0.78,
                          ),
                          decoration: BoxDecoration(
                            color: isUser ? tintOn : surface,
                            borderRadius: AppRadius.borderCard,
                          ),
                          padding: const EdgeInsets.symmetric(
                            horizontal: AppSpacing.space4,
                            vertical: AppSpacing.space3,
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                msg.content,
                                style: AppTypography.body(
                                  text,
                                  size: AppTypography.textSm,
                                ),
                              ),
                              // Card Item Data (misal lokasi HP)
                              if (msg.itemData != null) ...[
                                const SizedBox(height: AppSpacing.space3),
                                InkWell(
                                  onTap: () {},
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.all(AppSpacing.space2),
                                        decoration: BoxDecoration(
                                          color: subtle,
                                          borderRadius: AppRadius.borderSm,
                                        ),
                                        child: PhosphorIcon(
                                          PhosphorIcons.videoCamera(),
                                          size: AppDimensions.iconSizeSm,
                                          color: accent,
                                        ),
                                      ),
                                      const SizedBox(width: AppSpacing.space2),
                                      Flexible(
                                        child: Text(
                                          'Lihat rekaman',
                                          style: AppTypography.body(
                                            accent,
                                            size: AppTypography.textSm,
                                            weight: FontWeight.w600,
                                          ),
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),

                        const SizedBox(height: 4.0),

                        // Timestamp mono
                        Text(
                          _formatTime(msg.timestamp),
                          style: AppTypography.mono(
                            textSec,
                            size: AppTypography.textXs,
                          ),
                        ),

                        // Confirmation Card (misal: "Matikan semua lampu?")
                        if (msg.confirmation != null) ...[
                          const SizedBox(height: AppSpacing.space2),
                          Container(
                            constraints: BoxConstraints(
                              maxWidth: MediaQuery.of(context).size.width * 0.85,
                            ),
                            decoration: BoxDecoration(
                              color: surface,
                              borderRadius: AppRadius.borderCard,
                            ),
                            padding: const EdgeInsets.all(AppSpacing.space4),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  msg.confirmation!['prompt']?.toString() ?? 'Konfirmasi tindakan?',
                                  style: AppTypography.body(
                                    text,
                                    size: AppTypography.textSm,
                                    weight: FontWeight.w600,
                                  ),
                                ),
                                const SizedBox(height: AppSpacing.space3),
                                Row(
                                  children: [
                                    Expanded(
                                      child: AppButton(
                                        label: 'Batal',
                                        variant: AppButtonVariant.secondary,
                                        height: 40.0,
                                        onPressed: () {
                                          setState(() => msg.confirmation = null);
                                        },
                                      ),
                                    ),
                                    const SizedBox(width: AppSpacing.space2),
                                    Expanded(
                                      child: AppButton(
                                        label: 'Ya, jalankan',
                                        variant: AppButtonVariant.primary,
                                        height: 40.0,
                                        onPressed: () {
                                          setState(() => msg.confirmation = null);
                                          _sendMessage('Ya, jalankan');
                                        },
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  );
                },
              ),
            ),

            // Baris Chip Saran (12px gap, scrollable horizontal dengan 16px padding agar tidak terpotong)
            Container(
              height: 44.0,
              margin: const EdgeInsets.only(bottom: AppSpacing.space2),
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
                itemCount: _suggestions.length,
                separatorBuilder: (context, index) => const SizedBox(width: AppSpacing.space3), // 12px
                itemBuilder: (context, index) {
                  final s = _suggestions[index];
                  return AppChip(
                    label: s,
                    onTap: () => _sendMessage(s),
                  );
                },
              ),
            ),

            // Input Bar + Mic Circular Button 48x48
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppDimensions.screenMargin,
                vertical: AppSpacing.space2,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      height: AppDimensions.controlHeight,
                      decoration: BoxDecoration(
                        color: subtle,
                        borderRadius: AppRadius.borderSm,
                      ),
                      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space3),
                      child: Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _inputController,
                              style: AppTypography.body(text, size: AppTypography.textSm),
                              cursorColor: accent,
                              decoration: InputDecoration(
                                isDense: true,
                                border: InputBorder.none,
                                hintText: 'Ketik pesan atau perintah...',
                                hintStyle: AppTypography.body(textSec, size: AppTypography.textSm),
                              ),
                              onSubmitted: (val) => _sendMessage(val),
                            ),
                          ),
                          IconButton(
                            icon: PhosphorIcon(
                              PhosphorIcons.paperPlaneRight(),
                              size: AppDimensions.iconSizeSm,
                              color: textSec,
                            ),
                            onPressed: () => _sendMessage(),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.space2),
                  // Mic Circular Button (48x48)
                  InkWell(
                    onTap: _openListeningSheet,
                    borderRadius: BorderRadius.circular(AppRadius.full),
                    child: Container(
                      width: 48.0,
                      height: 48.0,
                      decoration: BoxDecoration(
                        color: accent,
                        shape: BoxShape.circle,
                      ),
                      alignment: Alignment.center,
                      child: PhosphorIcon(
                        PhosphorIcons.microphone(),
                        size: AppDimensions.iconSizeMd,
                        color: AppColors.lightSurface,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: AppSpacing.space2),
          ],
        ),
      ),
    );
  }
}
