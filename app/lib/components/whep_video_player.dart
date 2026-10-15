import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/theme/tokens.dart';

class WhepVideoPlayer extends StatefulWidget {
  final String whepUrl;
  final String? authToken;
  final Widget? fallbackWidget;
  final bool fitCover;

  const WhepVideoPlayer({
    super.key,
    required this.whepUrl,
    this.authToken,
    this.fallbackWidget,
    this.fitCover = true,
  });

  @override
  State<WhepVideoPlayer> createState() => _WhepVideoPlayerState();
}

class _WhepVideoPlayerState extends State<WhepVideoPlayer> {
  final RTCVideoRenderer _renderer = RTCVideoRenderer();
  RTCPeerConnection? _peerConnection;
  bool _isConnected = false;
  bool _hasError = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _initWebRtc();
  }

  Future<void> _initWebRtc() async {
    try {
      await _renderer.initialize();
      await _connectWhep();
    } catch (e) {
      if (mounted) {
        setState(() {
          _hasError = true;
          _errorMessage = e.toString();
        });
      }
    }
  }

  Future<void> _connectWhep() async {
    try {
      final configuration = <String, dynamic>{
        'iceServers': [
          {'urls': 'stun:stun.l.google.com:19302'},
        ],
        'sdpSemantics': 'unified-plan',
      };

      _peerConnection = await createPeerConnection(configuration);

      // Handle stream yang masuk
      _peerConnection!.onTrack = (RTCTrackEvent event) {
        if (event.streams.isNotEmpty && mounted) {
          setState(() {
            _renderer.srcObject = event.streams[0];
            _isConnected = true;
            _hasError = false;
          });
        }
      };

      // Tambahkan transceiver untuk menerima video saja
      await _peerConnection!.addTransceiver(
        kind: RTCRtpMediaType.RTCRtpMediaTypeVideo,
        init: RTCRtpTransceiverInit(direction: TransceiverDirection.RecvOnly),
      );

      // Buat SDP Offer WHEP
      final offer = await _peerConnection!.createOffer({
        'offerToReceiveVideo': 1,
        'offerToReceiveAudio': 0,
      });
      await _peerConnection!.setLocalDescription(offer);

      // Kirim SDP Offer ke endpoint WHEP MediaMTX via HTTP POST
      final dio = Dio();
      final headers = <String, dynamic>{
        'Content-Type': 'application/sdp',
      };
      if (widget.authToken != null && widget.authToken!.isNotEmpty) {
        headers['Authorization'] = 'Bearer ${widget.authToken}';
      }

      String targetUrl = widget.whepUrl;
      if (widget.authToken != null && widget.authToken!.isNotEmpty) {
        final uri = Uri.parse(widget.whepUrl);
        final queryParams = Map<String, dynamic>.from(uri.queryParameters);
        queryParams['token'] = widget.authToken!;
        targetUrl = uri.replace(queryParameters: queryParams).toString();
      }

      final response = await dio.post<String>(
        targetUrl,
        data: offer.sdp,
        options: Options(
          headers: headers,
          responseType: ResponseType.plain,
          validateStatus: (s) => s != null && s >= 200 && s < 300,
        ),
      );

      final answerSdp = response.data;
      if (answerSdp != null && answerSdp.isNotEmpty) {
        final answer = RTCSessionDescription(answerSdp, 'answer');
        await _peerConnection!.setRemoteDescription(answer);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _hasError = true;
          _errorMessage = e.toString();
        });
      }
    }
  }

  @override
  void dispose() {
    _peerConnection?.close();
    _peerConnection?.dispose();
    _renderer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_hasError || !_isConnected) {
      if (widget.fallbackWidget != null) {
        return Stack(
          fit: StackFit.expand,
          children: [
            widget.fallbackWidget!,
            if (!_hasError)
              Positioned(
                top: AppSpacing.space2,
                left: AppSpacing.space2,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space2, vertical: AppSpacing.space1),
                  decoration: BoxDecoration(
                    color: AppColors.darkSurface,
                    borderRadius: AppRadius.borderSm,
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const SizedBox(
                        width: 8,
                        height: 8,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                      const SizedBox(width: AppSpacing.space1),
                      Text(
                        'Menghubungkan WHEP...',
                        style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textXs),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        );
      }
      return Container(
        color: AppColors.darkBg,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(PhosphorIcons.broadcast(), size: AppDimensions.iconSizeMd, color: AppColors.statusWarn),
              const SizedBox(height: AppSpacing.space1),
              Text(
                _errorMessage ?? 'Menunggu Stream WebRTC (WHEP)...',
                style: AppTypography.body(AppColors.darkTextSecondary, size: AppTypography.textXs),
              ),
            ],
          ),
        ),
      );
    }

    return RTCVideoView(
      _renderer,
      objectFit: widget.fitCover
          ? RTCVideoViewObjectFit.RTCVideoViewObjectFitCover
          : RTCVideoViewObjectFit.RTCVideoViewObjectFitContain,
    );
  }
}
