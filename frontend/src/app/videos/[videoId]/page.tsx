'use client'

import { useState, useEffect, use } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { mockBackend } from '@/lib/mockBackend'
import { onVideoProgress, removeProgressCallback } from '@/lib/videoQueue'

interface Video {
  id: string
  title: string
  state: 'pending' | 'processing' | 'completed' | 'failed'
  output_url?: string
  duration: number
  created_at: string
  error_message?: string
  progress?: number
}

export default function VideoDetailPage({ params }: { params: Promise<{ videoId: string }> }) {
  const { videoId } = use(params)
  const router = useRouter()
  const [video, setVideo] = useState<Video | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const fetchVideo = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) {
          router.push('/auth/login')
          return
        }

        const data = await mockBackend.getVideo(videoId, token)
        setVideo(data)
        setProgress(data.progress || 0)
        setLoading(false)
      } catch (err: any) {
        setError('Failed to load video')
        setLoading(false)
      }
    }

    // Listen to real progress updates from video generation queue
    const handleProgressUpdate = (p: number) => {
      setProgress(p)
    }

    onVideoProgress(videoId, handleProgressUpdate)

    // Initial fetch
    fetchVideo()

    // Poll for updates if not completed
    const interval = setInterval(fetchVideo, 1000)

    return () => {
      clearInterval(interval)
      removeProgressCallback(videoId)
    }
  }, [videoId, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="spinner"></div>
          <p>Loading video...</p>
        </div>
      </div>
    )
  }

  if (error || !video) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error || 'Video not found'}</p>
          <Link href="/create" className="btn-tiktok">
            Create New Video
          </Link>
        </div>
      </div>
    )
  }

  const getStatusIcon = () => {
    switch (video.state) {
      case 'pending':
      case 'processing':
        return '⏳'
      case 'completed':
        return '✅'
      case 'failed':
        return '❌'
    }
  }

  const getStatusText = () => {
    switch (video.state) {
      case 'pending':
        return 'Waiting to start...'
      case 'processing':
        return 'Generating video...'
      case 'completed':
        return 'Ready to download!'
      case 'failed':
        return 'Generation failed'
    }
  }

  const downloadVideo = async () => {
    if (!video.output_url) return

    try {
      // Check if output_url is a blob URL or HTTP URL
      if (video.output_url.startsWith('blob:')) {
        // Already a blob URL, download directly
        const a = document.createElement('a')
        a.href = video.output_url
        a.download = `${video.title || 'video'}.mp4`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
      } else {
        // Try to fetch from URL
        const response = await fetch(video.output_url)
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${video.title || 'video'}.mp4`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      }
    } catch (err) {
      console.error('Download error:', err)
      alert('Failed to download video')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-bg via-dark-surface to-dark-bg">
      {/* Header */}
      <nav className="border-b border-dark-border sticky top-0 bg-dark-bg/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2">
            <div className="text-2xl">🎬</div>
            <h1 className="text-xl font-bold">Viral Video</h1>
          </Link>
          <div className="flex gap-4">
            <Link href="/create" className="hover:text-tiktok transition">
              Create New
            </Link>
            <Link href="/library" className="hover:text-tiktok transition">
              Library
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Status Card */}
        <div className="bg-dark-surface border border-dark-border rounded-lg p-8 mb-8">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">{video.title || 'Untitled Video'}</h1>
              <p className="text-gray-400">
                {new Date(video.created_at).toLocaleDateString()} •{' '}
                {video.duration} seconds
              </p>
            </div>
            <div className="text-4xl">{getStatusIcon()}</div>
          </div>

          {/* Progress Bar */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <p className="text-sm font-medium">{getStatusText()}</p>
              <p className="text-sm text-gray-400">{progress}%</p>
            </div>
            <div className="w-full bg-dark-bg rounded-full h-2">
              <div
                className="bg-gradient-to-r from-tiktok to-pink-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>

          {/* Error Message */}
          {video.state === 'failed' && video.error_message && (
            <div className="bg-red-500/10 border border-red-500 text-red-400 p-4 rounded mb-6">
              {video.error_message}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-4">
            {video.state === 'completed' && (
              <>
                <button onClick={downloadVideo} className="btn-tiktok">
                  Download MP4
                </button>
                <button className="btn-tiktok-outline">
                  Share to TikTok
                </button>
              </>
            )}
            {video.state === 'failed' && (
              <Link href="/create" className="btn-tiktok">
                Try Again
              </Link>
            )}
            <Link href="/library" className="btn-tiktok-outline">
              Back to Library
            </Link>
          </div>
        </div>

        {/* Video Preview */}
        {video.state === 'completed' && video.output_url && (
          <div className="bg-dark-surface border border-dark-border rounded-lg p-6 overflow-hidden">
            <h3 className="text-lg font-bold mb-4">Preview</h3>
            <video
              key={video.output_url}
              src={video.output_url}
              controls
              autoPlay
              className="w-full max-h-96 rounded-lg bg-black"
              style={{ maxWidth: '100%', height: 'auto' }}
            />
          </div>
        )}

        {/* Video Info */}
        <div className="mt-8 grid grid-cols-3 gap-4">
          <div className="bg-dark-surface border border-dark-border rounded-lg p-4 text-center">
            <p className="text-gray-400 text-sm mb-1">Duration</p>
            <p className="text-2xl font-bold">{video.duration}s</p>
          </div>
          <div className="bg-dark-surface border border-dark-border rounded-lg p-4 text-center">
            <p className="text-gray-400 text-sm mb-1">Status</p>
            <p className="text-2xl font-bold capitalize">{video.state}</p>
          </div>
          <div className="bg-dark-surface border border-dark-border rounded-lg p-4 text-center">
            <p className="text-gray-400 text-sm mb-1">Resolution</p>
            <p className="text-2xl font-bold">1080×1920</p>
          </div>
        </div>
      </div>
    </div>
  )
}
