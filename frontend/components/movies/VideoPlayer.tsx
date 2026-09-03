'use client';

import { useEffect, useRef, useState } from 'react';
import {
  Pause,
  Play,
  RotateCcw,
  RotateCw,
  Volume1,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2] as const;
const SKIP_SECONDS = 10;

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  const total = Math.floor(seconds);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const mm = h > 0 ? String(m).padStart(2, '0') : String(m);
  const ss = String(s).padStart(2, '0');
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

interface VideoPlayerProps {
  src: string;
  poster?: string;
  className?: string;
}

/**
 * A movie player with the controls a native <video> element doesn't
 * reliably expose: skip back/forward 10s, a full volume slider, a
 * playback-speed menu (up to 2x), and a scrub bar to jump anywhere.
 */
export function VideoPlayer({ src, poster, className }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const speedMenuRef = useRef<HTMLDivElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [speed, setSpeed] = useState<number>(1);
  const [isSpeedMenuOpen, setIsSpeedMenuOpen] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isScrubbing, setIsScrubbing] = useState(false);
  const [scrubTime, setScrubTime] = useState(0);

  // Wire up native video events -> React state.
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onTimeUpdate = () => {
      if (!isScrubbing) setCurrentTime(video.currentTime);
    };
    // 'seeked' fires after any seek (including programmatic ones made while
    // paused), which 'timeupdate' doesn't reliably do - without this, the
    // skip buttons would silently seek the video but leave the seek bar
    // and time readout looking unchanged whenever playback was paused.
    const onSeeked = () => setCurrentTime(video.currentTime);
    const onLoadedMetadata = () => setDuration(video.duration);
    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    const onEnded = () => setIsPlaying(false);
    const onVolumeChange = () => {
      setVolume(video.volume);
      setIsMuted(video.muted);
    };

    video.addEventListener('timeupdate', onTimeUpdate);
    video.addEventListener('seeked', onSeeked);
    video.addEventListener('loadedmetadata', onLoadedMetadata);
    video.addEventListener('play', onPlay);
    video.addEventListener('pause', onPause);
    video.addEventListener('ended', onEnded);
    video.addEventListener('volumechange', onVolumeChange);

    return () => {
      video.removeEventListener('timeupdate', onTimeUpdate);
      video.removeEventListener('seeked', onSeeked);
      video.removeEventListener('loadedmetadata', onLoadedMetadata);
      video.removeEventListener('play', onPlay);
      video.removeEventListener('pause', onPause);
      video.removeEventListener('ended', onEnded);
      video.removeEventListener('volumechange', onVolumeChange);
    };
  }, [isScrubbing]);

  // Close the speed menu on outside click.
  useEffect(() => {
    if (!isSpeedMenuOpen) return;
    function onDocClick(e: MouseEvent) {
      if (speedMenuRef.current && !speedMenuRef.current.contains(e.target as Node)) {
        setIsSpeedMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, [isSpeedMenuOpen]);

  function togglePlay() {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) video.play();
    else video.pause();
  }

  function skip(deltaSeconds: number) {
    const video = videoRef.current;
    if (!video) return;
    const cap = duration || video.duration || video.currentTime + deltaSeconds;
    const newTime = Math.min(Math.max(video.currentTime + deltaSeconds, 0), cap);
    video.currentTime = newTime;
    // Update state immediately - don't wait for a video event, since
    // 'timeupdate' skips paused video and 'seeked' can lag a tick.
    setCurrentTime(newTime);
  }

  function selectSpeed(rate: number) {
    const video = videoRef.current;
    if (video) video.playbackRate = rate;
    setSpeed(rate);
    setIsSpeedMenuOpen(false);
  }

  function toggleMute() {
    const video = videoRef.current;
    if (!video) return;
    video.muted = !video.muted;
  }

  function handleVolumeChange(e: React.ChangeEvent<HTMLInputElement>) {
    const video = videoRef.current;
    const next = Number(e.target.value);
    setVolume(next);
    if (video) {
      video.volume = next;
      video.muted = next === 0;
    }
  }

  function handleScrubStart() {
    setIsScrubbing(true);
    setScrubTime(currentTime);
  }

  function handleScrubChange(e: React.ChangeEvent<HTMLInputElement>) {
    setScrubTime(Number(e.target.value));
  }

  function handleScrubCommit() {
    const video = videoRef.current;
    if (video) video.currentTime = scrubTime;
    setCurrentTime(scrubTime);
    setIsScrubbing(false);
  }

  const displayedTime = isScrubbing ? scrubTime : currentTime;
  const VolumeIcon = isMuted || volume === 0 ? VolumeX : volume < 0.5 ? Volume1 : Volume2;

  return (
    <div className={cn('group relative overflow-hidden rounded-xl bg-black', className)}>
      <video
        ref={videoRef}
        src={src}
        poster={poster || undefined}
        className="aspect-video w-full"
        onClick={togglePlay}
      >
        Your browser doesn&apos;t support video playback.
      </video>

      {/* Center play/pause overlay, shown when paused */}
      {!isPlaying && (
        <button
          type="button"
          onClick={togglePlay}
          aria-label="Play"
          className="absolute inset-0 flex items-center justify-center bg-black/20 transition-colors hover:bg-black/30"
        >
          <span className="flex h-16 w-16 items-center justify-center rounded-full bg-white/90 text-black">
            <Play size={28} className="ml-1 fill-current" />
          </span>
        </button>
      )}

      {/* Control bar */}
      <div className="absolute inset-x-0 bottom-0 z-10 flex flex-col gap-1.5 bg-gradient-to-t from-black/85 via-black/50 to-transparent px-3 pb-2 pt-8">
        <input
          type="range"
          min={0}
          max={duration || 0}
          step={0.1}
          value={displayedTime}
          onMouseDown={handleScrubStart}
          onTouchStart={handleScrubStart}
          onChange={handleScrubChange}
          onMouseUp={handleScrubCommit}
          onTouchEnd={handleScrubCommit}
          aria-label="Seek"
          className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-white/25 accent-accent"
        />

        <div className="flex items-center gap-3 text-white">
          <button type="button" onClick={togglePlay} aria-label={isPlaying ? 'Pause' : 'Play'} className="hover:text-accent">
            {isPlaying ? <Pause size={18} className="fill-current" /> : <Play size={18} className="fill-current" />}
          </button>

          <button type="button" onClick={() => skip(-SKIP_SECONDS)} aria-label={`Back ${SKIP_SECONDS} seconds`} className="hover:text-accent">
            <RotateCcw size={17} />
          </button>

          <button type="button" onClick={() => skip(SKIP_SECONDS)} aria-label={`Forward ${SKIP_SECONDS} seconds`} className="hover:text-accent">
            <RotateCw size={17} />
          </button>

          {/* Volume: icon toggles mute, slider sets level - like native controls */}
          <div className="flex items-center gap-1.5">
            <button type="button" onClick={toggleMute} aria-label={isMuted ? 'Unmute' : 'Mute'} className="hover:text-accent">
              <VolumeIcon size={17} />
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              aria-label="Volume"
              className="h-1 w-16 cursor-pointer appearance-none rounded-full bg-white/25 accent-accent"
            />
          </div>

          <span className="font-mono text-xs tabular-nums text-white/80">
            {formatTime(displayedTime)} / {formatTime(duration)}
          </span>

          {/* Speed menu */}
          <div ref={speedMenuRef} className="relative ml-auto">
            <button
              type="button"
              onClick={() => setIsSpeedMenuOpen((v) => !v)}
              aria-label="Playback speed"
              aria-expanded={isSpeedMenuOpen}
              className="rounded border border-white/30 px-2 py-0.5 font-mono text-xs hover:border-accent hover:text-accent"
            >
              {speed}x
            </button>

            {isSpeedMenuOpen && (
              <div className="absolute bottom-full right-0 mb-2 flex flex-col rounded-lg border border-white/15 bg-black/95 py-1 shadow-xl">
                {SPEEDS.map((rate) => (
                  <button
                    key={rate}
                    type="button"
                    onClick={() => selectSpeed(rate)}
                    className={cn(
                      'px-4 py-1.5 text-left font-mono text-xs whitespace-nowrap hover:bg-white/10',
                      rate === speed ? 'text-accent' : 'text-white'
                    )}
                  >
                    {rate}x
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
