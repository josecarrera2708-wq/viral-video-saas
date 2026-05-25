'use client'

import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-bg via-dark-surface to-dark-bg">
      {/* Navigation */}
      <nav className="border-b border-dark-border">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="text-2xl font-bold text-tiktok">🎬</div>
            <h1 className="text-xl font-bold">Viral Video SaaS</h1>
          </div>
          <div className="flex gap-4">
            <Link href="/auth/login" className="hover:text-tiktok transition">
              Login
            </Link>
            <Link href="/auth/signup" className="btn-tiktok px-4 py-2">
              Sign Up
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 py-20 text-center">
        <h2 className="text-5xl font-bold mb-6">
          Create Viral TikTok Videos in <span className="text-gradient">30 Seconds</span>
        </h2>
        <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
          Generate professional AI-powered videos. Customize with text, music, and effects.
          Upload to TikTok and watch your content go viral.
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/auth/signup" className="btn-tiktok px-8 py-3">
            Start Free
          </Link>
          <button className="btn-tiktok-outline px-8 py-3">
            Watch Demo
          </button>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-4 py-20">
        <h3 className="text-3xl font-bold text-center mb-12">Why Choose Us?</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            {
              icon: '⚡',
              title: 'Lightning Fast',
              desc: 'Generate videos in 30-60 seconds, not hours',
            },
            {
              icon: '🎨',
              title: '100+ Templates',
              desc: 'Pre-designed templates for every niche and style',
            },
            {
              icon: '💰',
              title: 'Affordable',
              desc: 'Freemium model. Create videos for just a few cents',
            },
            {
              icon: '🤖',
              title: 'AI-Powered',
              desc: 'Professional quality using latest AI models',
            },
            {
              icon: '📱',
              title: 'TikTok Ready',
              desc: 'Optimized for 1080x1920 format and trending sounds',
            },
            {
              icon: '🚀',
              title: 'Easy to Use',
              desc: 'No technical skills required. Drag, drop, create',
            },
          ].map((feature, idx) => (
            <div key={idx} className="bg-dark-surface border border-dark-border rounded-lg p-6 text-center">
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h4 className="text-xl font-bold mb-2">{feature.title}</h4>
              <p className="text-gray-400">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-7xl mx-auto px-4 py-20">
        <h3 className="text-3xl font-bold text-center mb-12">Simple Pricing</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            {
              name: 'Free',
              price: '$0',
              desc: 'Perfect for testing',
              features: ['5 videos/month', 'Basic templates', 'Watermark'],
            },
            {
              name: 'Creator',
              price: '$9.99',
              desc: 'Most popular',
              features: ['50 credits/month', 'All templates', 'No watermark', 'Priority support'],
              highlighted: true,
            },
            {
              name: 'Business',
              price: '$99',
              desc: 'For agencies',
              features: ['500 credits/month', 'API access', 'White-label', 'Analytics'],
            },
          ].map((plan, idx) => (
            <div
              key={idx}
              className={`rounded-lg p-8 border ${
                plan.highlighted
                  ? 'bg-tiktok/10 border-tiktok'
                  : 'bg-dark-surface border-dark-border'
              }`}
            >
              <h4 className="text-2xl font-bold mb-2">{plan.name}</h4>
              <p className="text-gray-400 mb-4">{plan.desc}</p>
              <div className="text-4xl font-bold text-tiktok mb-6">{plan.price}</div>
              <ul className="space-y-2 mb-6">
                {plan.features.map((feature, i) => (
                  <li key={i} className="text-sm text-gray-300">
                    ✓ {feature}
                  </li>
                ))}
              </ul>
              <button className={plan.highlighted ? 'btn-tiktok' : 'btn-tiktok-outline'}>
                Get Started
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-tiktok/10 border-t border-dark-border py-20">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h3 className="text-3xl font-bold mb-4">Ready to Create?</h3>
          <p className="text-xl text-gray-400 mb-8">
            Join thousands of creators making viral videos every day.
          </p>
          <Link href="/auth/signup" className="btn-tiktok px-8 py-3 inline-block">
            Start Your Free Trial
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-dark-border py-8 text-center text-gray-500 text-sm">
        <p>© 2026 Viral Video SaaS. All rights reserved.</p>
      </footer>
    </div>
  )
}
