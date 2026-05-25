'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { mockBackend } from '@/lib/mockBackend'

interface Video {
  id: string
  title: string
  duration: number
  state: string
  created_at: string
  output_url?: string
}

export default function LibraryPage() {
  const router = useRouter()
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchVideos = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) {
          router.push('/auth/login')
          return
        }

        const data = await mockBackend.listVideos(token)
        setVideos(data as Video[])
        setLoading(false)
      } catch (err: any) {
        setError('Failed to load videos')
        setLoading(false)
      }
    }

    fetchVideos()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    )
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
            <Link href="/create" className="btn-tiktok px-4 py-2">
              New Video
            </Link>
            <Link href="/account" className="hover:text-tiktok transition">
              Account
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold mb-12">My Videos</h1>

        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-400 p-4 rounded-lg mb-8">
            {error}
          </div>
        )}

        {videos.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">🎬</div>
            <h2 className="text-2xl font-bold mb-2">No videos yet</h2>
            <p className="text-gray-400 mb-8">
              Create your first viral video in seconds
            </p>
            <Link href="/create" className="btn-tiktok inline-block">
              Create Video
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {videos.map((video) => (
              <Link
                key={video.id}
                href={`/videos/${video.id}`}
                className="bg-dark-surface border border-dark-border rounded-lg overflow-hidden hover:border-tiktok transition group cursor-pointer"
              >
                {/* Thumbnail */}
                <div className="aspect-video bg-dark-bg flex items-center justify-center relative overflow-hidden">
                  {video.state === 'completed' && video.output_url ? (
                    <video
                      src={video.output_url}
                      className="w-full h-full object-cover group-hover:scale-105 transition"
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center w-full h-full">
                      {video.state === 'pending' && (
                        <>
                          <div className="spinner mb-3"></div>
                          <p className="text-sm text-gray-400">Queued</p>
                        </>
                      )}
                      {video.state === 'processing' && (
                        <>
                          <div className="spinner mb-3"></div>
                          <p className="text-sm text-gray-400">Generating...</p>
                        </>
                      )}
                      {video.state === 'failed' && (
                        <>
                          <p className="text-2xl mb-2">❌</p>
                          <p className="text-sm text-red-400">Failed</p>
                        </>
                      )}
                    </div>
                  )}

                  {/* Status Badge */}
                  <div className="absolute top-2 right-2 bg-dark-bg/80 backdrop-blur px-3 py-1 rounded-full text-xs font-medium capitalize">
                    {video.state === 'completed' ? '✓ Ready' : video.state}
                  </div>
                </div>

                {/* Info */}
                <div className="p-4">
                  <h3 className="font-bold mb-2 line-clamp-2">{video.title || 'Untitled'}</h3>
                  <div className="flex items-center justify-between text-sm text-gray-400">
                    <span>{video.duration}s</span>
                    <span>{new Date(video.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
