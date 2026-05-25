'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { mockBackend } from '@/lib/mockBackend'

interface User {
  id: string
  email: string
  name: string
  credits_balance: number
  subscription_tier: string
}

interface Transaction {
  id: string
  amount: number
  type: string
  reason: string
  created_at: string
}

export default function AccountPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) {
          router.push('/auth/login')
          return
        }

        const userData = await mockBackend.getMe(token)
        setUser(userData)

        const txData = await mockBackend.getTransactions(token)
        setTransactions(txData.transactions || [])

        setLoading(false)
      } catch (err: any) {
        setError('Failed to load account')
        setLoading(false)
      }
    }

    fetchUser()
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    router.push('/')
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
      {/* Header */}
      <nav className="border-b border-dark-border sticky top-0 bg-dark-bg/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2">
            <div className="text-2xl">🎬</div>
            <h1 className="text-xl font-bold">Viral Video</h1>
          </Link>
          <div className="flex gap-4">
            <Link href="/create" className="hover:text-tiktok transition">
              Create
            </Link>
            <Link href="/library" className="hover:text-tiktok transition">
              Library
            </Link>
            <button onClick={handleLogout} className="text-gray-400 hover:text-white transition">
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold mb-12">Account Settings</h1>

        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-400 p-4 rounded-lg mb-8">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sidebar */}
          <div className="space-y-6">
            {/* Profile Card */}
            {user && (
              <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
                <h3 className="text-lg font-bold mb-4">Profile</h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-gray-400 text-sm">Name</p>
                    <p className="font-medium">{user.name}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-sm">Email</p>
                    <p className="font-medium">{user.email}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Credits Card */}
            {user && (
              <div className="bg-dark-surface border border-tiktok/20 rounded-lg p-6">
                <h3 className="text-lg font-bold mb-4">Credits</h3>
                <div className="mb-6">
                  <p className="text-gray-400 text-sm mb-1">Available</p>
                  <p className="text-4xl font-bold text-tiktok">{user.credits_balance}</p>
                  <p className="text-gray-500 text-xs mt-1">
                    Subscription: {user.subscription_tier}
                  </p>
                </div>
                <Link href="/billing" className="btn-tiktok">
                  Buy Credits
                </Link>
              </div>
            )}
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Transaction History */}
            <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
              <h3 className="text-lg font-bold mb-6">Transaction History</h3>

              {transactions.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <p>No transactions yet</p>
                  <Link href="/billing" className="text-tiktok hover:underline mt-2 block">
                    Purchase credits to get started
                  </Link>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b border-dark-border">
                      <tr>
                        <th className="text-left py-3 px-3 font-medium text-sm">Date</th>
                        <th className="text-left py-3 px-3 font-medium text-sm">Type</th>
                        <th className="text-left py-3 px-3 font-medium text-sm">Amount</th>
                        <th className="text-left py-3 px-3 font-medium text-sm">Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((tx) => (
                        <tr key={tx.id} className="border-b border-dark-border/30">
                          <td className="py-3 px-3 text-sm">
                            {new Date(tx.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-3 text-sm">
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium ${
                                tx.amount > 0
                                  ? 'bg-green-500/20 text-green-400'
                                  : 'bg-red-500/20 text-red-400'
                              }`}
                            >
                              {tx.amount > 0 ? '+' : ''}{tx.amount}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-sm capitalize">{tx.type}</td>
                          <td className="py-3 px-3 text-sm text-gray-400">
                            {tx.reason.replace(/_/g, ' ')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
