/**
 * Sound Service - Audio Manager for Sathi UI & Background Atmosphere
 */

const UI_SOUNDS = {
  wake: '/sounds/ui/companion_wake.mp3',
  listening: '/sounds/ui/listening.mp3',
  response: '/sounds/ui/Response.mp3',
  task_complete: '/sounds/ui/TaskComplete.mp3',
  chapter_complete: '/sounds/ui/chapterComplete.mp3',
  meditation_complete: '/sounds/ui/meditationComplete.mp3',
  ident: '/sounds/ui/A_unique_audio_ident_#1-1791121186911.mp3',
};

const MUSIC_TRACKS = {
  companion_atmosphere: '/sounds/music/Companion_Atmosphere.mp3',
  companion_atmosphere_alt: '/sounds/music/Companion_Atmosphere2.mp3',
  study_space: '/sounds/music/Sathi_Study_Space.mp3',
  deep_focus_1: '/sounds/music/DeepFocus1.mp3',
  deep_focus_2: '/sounds/music/Deepfocus2.mp3',
  sanctuary_1: '/sounds/music/Santury.mp3',
  sanctuary_2: '/sounds/music/Santury2.mp3',
};

let activeMusicAudio = null;
let currentMusicTrack = null;

export const soundService = {
  /**
   * Play a short UI sound effect
   */
  playSound(soundKey, volume = 0.6) {
    try {
      const src = UI_SOUNDS[soundKey];
      if (!src) return;
      const audio = new Audio(src);
      audio.volume = volume;
      audio.play().catch((err) => {
        // Autoplay restrictions or user interaction handling
        console.debug('UI sound playback skipped:', err.message);
      });
    } catch (err) {
      console.warn('Error playing sound effect:', err);
    }
  },

  /**
   * Start ambient background music
   */
  playMusic(trackKey, volume = 0.2, loop = true) {
    try {
      const src = MUSIC_TRACKS[trackKey] || MUSIC_TRACKS.companion_atmosphere;
      if (activeMusicAudio && currentMusicTrack === trackKey) {
        return; // Already playing this track
      }
      this.stopMusic();

      activeMusicAudio = new Audio(src);
      activeMusicAudio.volume = volume;
      activeMusicAudio.loop = loop;
      currentMusicTrack = trackKey;
      activeMusicAudio.play().catch((err) => {
        console.debug('Music autoplay restricted until user gesture:', err.message);
      });
    } catch (err) {
      console.warn('Error playing background music:', err);
    }
  },

  /**
   * Stop active background music
   */
  stopMusic() {
    if (activeMusicAudio) {
      activeMusicAudio.pause();
      activeMusicAudio.currentTime = 0;
      activeMusicAudio = null;
      currentMusicTrack = null;
    }
  },
};
