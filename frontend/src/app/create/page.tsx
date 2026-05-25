'use client'

import { useState, useRef } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { mockBackend } from '@/lib/mockBackend'

const TEMPLATES = [
  { id: 'realistic', name: 'Realistic', icon: '🎬' },
  { id: 'cinematic', name: 'Cinematic', icon: '🎥' },
  { id: 'anime', name: 'Anime', icon: '✨' },
  { id: 'artistic', name: 'Artistic', icon: '🎨' },
  { id: 'horror', name: 'Horror', icon: '👻' },
  { id: 'comedy', name: 'Comedy', icon: '😂' },
]

export default function CreatePage() {
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [image, setImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string>('')
  const [title, setTitle] = useState('')
  const [subtitle, setSubtitle] = useState('')
  const [script, setScript] = useState('')
  const [duration, setDuration] = useState(15)
  const [template, setTemplate] = useState('realistic')
  const [language, setLanguage] = useState('es')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (file.size > 50 * 1024 * 1024) {
      setError('Image too large (max 50MB)')
      return
    }

    setImage(file)
    setError('')

    // Preview
    const reader = new FileReader()
    reader.onload = (event) => {
      setImagePreview(event.target?.result as string)
    }
    reader.readAsDataURL(file)
  }

  const calculateCredits = (): number => {
    return 30 + Math.round(duration * 0.07)
  }

  const handleCreateVideo = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      // Get auth token
      const token = localStorage.getItem('token')
      if (!token) {
        router.push('/auth/login')
        return
      }

      if (!image) {
        setError('Please select an image')
        setLoading(false)
        return
      }

      // Call mock backend
      const result = await mockBackend.createVideo(
        token,
        title,
        subtitle,
        script,
        duration,
        template,
        language,
        image
      )

      // Redirect to video detail page
      router.push(`/videos/${result.id}`)
    } catch (err: any) {
      setError(err.message || 'An error occurred')
      setLoading(false)
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
          <Link href="/library" className="hover:text-tiktok transition">
            My Videos
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold mb-2">Create Your Viral Video</h1>
        <p className="text-gray-400 mb-8">Upload an image and let AI do the magic</p>

        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-400 p-4 rounded-lg mb-8">
            {error}
          </div>
        )}

        <form onSubmit={handleCreateVideo} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Upload & Preview */}
          <div className="space-y-6">
            {/* Image Upload */}
            <div className="bg-dark-surface border-2 border-dashed border-dark-border rounded-lg p-8">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                className="hidden"
              />

              {!imagePreview ? (
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full flex flex-col items-center justify-center py-12 cursor-pointer hover:opacity-80 transition"
                >
                  <div className="text-5xl mb-4">📸</div>
                  <p className="text-lg font-medium mb-2">Upload Image</p>
                  <p className="text-gray-400 text-sm">JPG, PNG, or WEBP (max 50MB)</p>
                </button>
              ) : (
                <div className="space-y-4">
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="w-full rounded-lg max-h-96 object-cover"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full btn-tiktok-outline"
                  >
                    Change Image
                  </button>
                </div>
              )}
            </div>

            {/* Templates */}
            <div>
              <label className="block text-sm font-medium mb-3">Video Style</label>
              <div className="grid grid-cols-2 gap-3">
                {TEMPLATES.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setTemplate(t.id)}
                    className={`p-3 rounded-lg border-2 transition ${
                      template === t.id
                        ? 'border-tiktok bg-tiktok/10'
                        : 'border-dark-border hover:border-tiktok'
                    }`}
                  >
                    <div className="text-2xl mb-1">{t.icon}</div>
                    <div className="text-sm font-medium">{t.name}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Form Inputs */}
          <div className="space-y-6">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium mb-2">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value.slice(0, 50))}
                placeholder="e.g., INCREDIBLE MOMENT"
                maxLength={50}
              />
              <p className="text-gray-500 text-xs mt-1">{title.length}/50</p>
            </div>

            {/* Subtitle */}
            <div>
              <label className="block text-sm font-medium mb-2">Subtitle</label>
              <input
                type="text"
                value={subtitle}
                onChange={(e) => setSubtitle(e.target.value.slice(0, 50))}
                placeholder="e.g., Watch until the end"
                maxLength={50}
              />
              <p className="text-gray-500 text-xs mt-1">{subtitle.length}/50</p>
            </div>

            {/* Script/Narration */}
            <div>
              <label className="block text-sm font-medium mb-2">Script (Narration)</label>
              <textarea
                value={script}
                onChange={(e) => setScript(e.target.value.slice(0, 500))}
                placeholder="Write what you want the AI to say..."
                maxLength={500}
                rows={6}
              />
              <p className="text-gray-500 text-xs mt-1">{script.length}/500</p>
            </div>

            {/* Duration */}
            <div>
              <label className="block text-sm font-medium mb-3">Duration</label>
              <div className="flex gap-3">
                {[15, 30, 60].map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setDuration(d)}
                    className={`flex-1 py-2 rounded-lg border-2 transition ${
                      duration === d
                        ? 'border-tiktok bg-tiktok/10'
                        : 'border-dark-border hover:border-tiktok'
                    }`}
                  >
                    {d}s
                  </button>
                ))}
              </div>
            </div>

            {/* Language */}
            <div>
              <label className="block text-sm font-medium mb-2">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full"
              >
                <option value="es">Spanish</option>
                <option value="en">English</option>
                <option value="pt">Portuguese</option>
                <option value="fr">French</option>
              </select>
            </div>

            {/* Credit Cost */}
            <div className="bg-dark-surface border border-tiktok/20 rounded-lg p-4">
              <p className="text-sm text-gray-400 mb-1">Estimated Cost</p>
              <p className="text-2xl font-bold text-tiktok">{calculateCredits()} credits</p>
              <p className="text-xs text-gray-500 mt-1">
                Overhead: 30 + ({duration} × $0.07)
              </p>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading || !image}
              className="btn-tiktok disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating Video...' : 'Create Video'}
            </button>

            <p className="text-xs text-gray-500 text-center">
              Video generation typically takes 2-3 minutes
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}
