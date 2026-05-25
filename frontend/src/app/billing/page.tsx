'use client'

import { useState, useEffect, Suspense } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { mockBackend } from '@/lib/mockBackend'

interface Package {
  id: string
  name: string
  credits: number
  price_usd: number
  price_per_credit: number
}

function BillingContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [packages, setPackages] = useState<Package[]>([])
  const [loading, setLoading] = useState(true)
  const [checkoutLoading, setCheckoutLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    const fetchPackages = async () => {
      try {
        const data = await mockBackend.getPackages()
        setPackages(data.packages || [])
        setLoading(false)

        if (searchParams.get('success')) {
          setSuccess(true)
        }
      } catch (err: any) {
        setError('Failed to load packages')
        setLoading(false)
      }
    }

    fetchPackages()
  }, [searchParams])

  const handleCheckout = async (packageId: string) => {
    setCheckoutLoading(true)
    setError('')

    try {
      const token = localStorage.getItem('token')
      if (!token) {
        router.push('/auth/login')
        return
      }

      await mockBackend.checkout(packageId, token)
      setSuccess(true)
      setCheckoutLoading(false)
    } catch (err: any) {
      setError(err.message || 'An error occurred')
      setCheckoutLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-bg via-dark-surface to-dark-bg">
      <nav className="border-b border-dark-border sticky top-0 bg-dark-bg/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2">
            <div className="text-2xl">🎬</div>
            <h1 className="text-xl font-bold">Viral Video</h1>
          </Link>
          <Link href="/account" className="hover:text-tiktok transition">
            Back to Account
          </Link>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold mb-4">Buy Credits</h1>
        <p className="text-gray-400 mb-12">
          Choose a package and upgrade your account instantly
        </p>

        {success && (
          <div className="bg-green-500/10 border border-green-500 text-green-400 p-4 rounded-lg mb-8">
            Payment successful! Your credits have been added to your account.
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-400 p-4 rounded-lg mb-8">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          {packages.map((pkg) => (
            <div
              key={pkg.id}
              className="bg-dark-surface border-2 border-dark-border rounded-lg p-8 hover:border-tiktok transition flex flex-col"
            >
              <h3 className="text-2xl font-bold mb-2">{pkg.name}</h3>
              <p className="text-gray-400 text-sm mb-6">
                ${pkg.price_per_credit.toFixed(2)} per credit
              </p>

              <div className="mb-8">
                <p className="text-5xl font-bold text-tiktok">{pkg.credits}</p>
                <p className="text-gray-400 text-sm">credits</p>
              </div>

              <div className="mb-8 flex-grow">
                <p className="text-gray-400 text-sm mb-3">Perfect for:</p>
                <ul className="space-y-2 text-sm">
                  {pkg.id === 'basic' && (
                    <>
                      <li>✓ Casual creators</li>
                      <li>✓ ~7-10 videos</li>
                      <li>✓ Personal projects</li>
                    </>
                  )}
                  {pkg.id === 'pro' && (
                    <>
                      <li>✓ Active creators</li>
                      <li>✓ ~18-20 videos</li>
                      <li>✓ Best value</li>
                    </>
                  )}
                  {pkg.id === 'business' && (
                    <>
                      <li>✓ Agencies</li>
                      <li>✓ 50+ videos</li>
                      <li>✓ Enterprise support</li>
                    </>
                  )}
                </ul>
              </div>

              <div className="space-y-3">
                <p className="text-2xl font-bold">${pkg.price_usd}</p>
                <button
                  onClick={() => handleCheckout(pkg.id)}
                  disabled={checkoutLoading}
                  className="btn-tiktok disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {checkoutLoading ? 'Processing...' : 'Buy Now'}
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-dark-surface border border-dark-border rounded-lg p-8">
          <h2 className="text-2xl font-bold mb-6">Frequently Asked Questions</h2>

          <div className="space-y-6">
            <div>
              <h3 className="font-bold mb-2">How are credits calculated?</h3>
              <p className="text-gray-400">
                Each video costs 30 credits + (duration in seconds × 0.07). For example, a 30-second
                video costs 30 + (30 × 0.07) = 32.1 credits.
              </p>
            </div>

            <div>
              <h3 className="font-bold mb-2">Do credits expire?</h3>
              <p className="text-gray-400">
                No, credits don't expire. Use them whenever you want. They're tied to your account
                permanently.
              </p>
            </div>

            <div>
              <h3 className="font-bold mb-2">Can I get a refund?</h3>
              <p className="text-gray-400">
                We offer refunds within 30 days if you're not satisfied. Contact support for more
                information.
              </p>
            </div>

            <div>
              <h3 className="font-bold mb-2">What payment methods do you accept?</h3>
              <p className="text-gray-400">
                We accept all major credit cards (Visa, Mastercard, American Express) via Stripe.
              </p>
            </div>

            <div>
              <h3 className="font-bold mb-2">Is my payment secure?</h3>
              <p className="text-gray-400">
                Yes, we use Stripe for payments, which is PCI DSS Level 1 certified. Your payment
                information is never stored on our servers.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function BillingPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="spinner"></div>
        </div>
      }
    >
      <BillingContent />
    </Suspense>
  )
}
