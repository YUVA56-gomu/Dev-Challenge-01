import { synthesizeVoice } from './api';

class VoiceService {
  constructor() {
    this.currentAudio = null;
    this.isSpeaking = false;
    this.isPaused = false;
    this.activeUtterance = null;
    this.activeText = null;
    this.blobCache = new Map(); // In-memory cache for audio blobs: text -> blob
    this.lastUsedFallback = false;
  }

  /**
   * Speaks text using ElevenLabs TTS (via backend) with automatic fallback to Web Speech API.
   * @param {string} text - Text to synthesize and speak
   * @param {function} onStart - Callback when audio playback starts
   * @param {function} onEnd - Callback when audio playback finishes
   * @param {function} onFallback - Callback if falling back to device/browser voice
   */
  async speak(text, onStart = () => {}, onEnd = () => {}, onFallback = () => {}) {
    this.stop();

    if (!text || !text.trim()) {
      onEnd();
      return;
    }

    // Clean text: strip markdown symbols, pipes, format currency
    const cleanText = text
      .replace(/[#*_`~>-]/g, '')
      .replace(/\[(.*?)\]\(.*?\)/g, '$1')
      .replace(/₹/g, 'Rupees ')
      .trim();

    this.activeText = cleanText;

    // 1. Check in-memory audio blob cache first (avoids network call & preserves credits)
    if (this.blobCache.has(cleanText)) {
      try {
        const cachedBlob = this.blobCache.get(cleanText);
        await this._playBlobAudio(cachedBlob, onStart, onEnd);
        return;
      } catch (err) {
        console.warn('Playback of cached blob failed, re-fetching:', err);
      }
    }

    try {
      // 2. Attempt synthesis through backend (which checks SHA-256 disk cache or calls ElevenLabs)
      const result = await synthesizeVoice(cleanText);

      if (result.type === 'audio' && result.blob) {
        this.lastUsedFallback = false;
        this.blobCache.set(cleanText, result.blob);
        await this._playBlobAudio(result.blob, onStart, onEnd);
        return;
      }
    } catch (err) {
      console.warn('ElevenLabs backend synthesis error, falling back to browser speech:', err);
    }

    // 3. Graceful Fallback: Browser Web Speech API
    this.lastUsedFallback = true;
    onFallback('Voice service unavailable — using device voice.');
    this._fallbackBrowserSpeech(cleanText, onStart, onEnd);
  }

  async _playBlobAudio(blob, onStart, onEnd) {
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);
    this.currentAudio = audio;

    audio.onplay = () => {
      this.isSpeaking = true;
      this.isPaused = false;
      onStart();
    };

    audio.onpause = () => {
      if (this.currentAudio === audio && !audio.ended) {
        this.isPaused = true;
      }
    };

    audio.onended = () => {
      this.isSpeaking = false;
      this.isPaused = false;
      URL.revokeObjectURL(audioUrl);
      if (this.currentAudio === audio) {
        this.currentAudio = null;
      }
      onEnd();
    };

    audio.onerror = (e) => {
      console.warn('Audio element error, falling back to device speech:', e);
      URL.revokeObjectURL(audioUrl);
      this._fallbackBrowserSpeech(this.activeText, onStart, onEnd);
    };

    await audio.play();
  }

  _fallbackBrowserSpeech(text, onStart, onEnd) {
    if (!('speechSynthesis' in window)) {
      console.warn('Web Speech API is not supported on this browser.');
      this.isSpeaking = false;
      this.isPaused = false;
      onEnd();
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.05;

    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(
      (v) => v.lang.includes('en-IN') || v.lang.includes('en-GB') || v.name.includes('Natural')
    );
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    utterance.onstart = () => {
      this.isSpeaking = true;
      this.isPaused = false;
      onStart();
    };

    utterance.onpause = () => {
      this.isPaused = true;
    };

    utterance.onresume = () => {
      this.isPaused = false;
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      this.isPaused = false;
      this.activeUtterance = null;
      onEnd();
    };

    utterance.onerror = () => {
      this.isSpeaking = false;
      this.isPaused = false;
      this.activeUtterance = null;
      onEnd();
    };

    this.activeUtterance = utterance;
    window.speechSynthesis.speak(utterance);
  }

  pause() {
    if (this.currentAudio && !this.currentAudio.paused) {
      this.currentAudio.pause();
      this.isPaused = true;
    } else if (window.speechSynthesis && window.speechSynthesis.speaking) {
      window.speechSynthesis.pause();
      this.isPaused = true;
    }
  }

  resume() {
    if (this.currentAudio && this.currentAudio.paused) {
      this.currentAudio.play().catch(console.error);
      this.isPaused = false;
    } else if (window.speechSynthesis && window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      this.isPaused = false;
    }
  }

  replay(text, onStart, onEnd, onFallback) {
    return this.speak(text || this.activeText, onStart, onEnd, onFallback);
  }

  stop() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    this.isSpeaking = false;
    this.isPaused = false;
    this.activeUtterance = null;
  }

  /**
   * Initializes browser Speech-to-Text (STT) if supported.
   * Streams transcript to user input without prematurely auto-sending.
   */
  createSpeechRecognizer(onTranscript, onError, onEnd) {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      return {
        isSupported: false,
        start: () => onError('Speech recognition is not supported in this browser. Please use text input.'),
        stop: () => {},
      };
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-IN'; // Indian English tailored for CA terms

    recognition.onresult = (event) => {
      let currentTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        currentTranscript += event.results[i][0].transcript;
      }
      const isFinal = Boolean(event.results[0] && event.results[0].isFinal);
      onTranscript(currentTranscript, isFinal);
    };

    recognition.onerror = (event) => {
      let message = 'Speech recognition error';
      if (event.error === 'not-allowed') {
        message = 'Microphone permission denied. Please allow microphone access in your browser.';
      } else if (event.error === 'audio-capture') {
        message = 'No microphone found. Please connect a microphone.';
      } else if (event.error === 'network') {
        message = 'Speech recognition network error.';
      } else if (event.error === 'no-speech') {
        message = 'No speech detected. Please try speaking again.';
      }
      onError(message);
    };

    recognition.onend = () => {
      onEnd();
    };

    return {
      isSupported: true,
      start: () => {
        try {
          recognition.start();
        } catch (e) {
          // Already active
        }
      },
      stop: () => {
        try {
          recognition.stop();
        } catch (e) {}
      },
    };
  }
}

export const voiceService = new VoiceService();

