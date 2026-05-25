import { NextRequest, NextResponse } from 'next/server'
import { v4 as uuidv4 } from 'uuid'

// In-memory database
const users: any = {}
const videos: any = {}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { email, password, name } = body

    if (!email || !password || !name) {
      return NextResponse.json(
        { detail: 'Missing required fields' },
        { status: 400 }
      )
    }

    if (users[email]) {
      return NextResponse.json(
        { detail: 'Email already registered' },
        { status: 400 }
      )
    }

    const userId = uuidv4()
    users[email] = {
      id: userId,
      email,
      name,
      password,
      credits_balance: 100,
      subscription_tier: 'free',
      created_at: new Date().toISOString(),
    }

    return NextResponse.json(
      {
        access_token: `token_${userId}`,
        token_type: 'bearer',
        user: {
          id: userId,
          email,
          name,
          credits_balance: 100,
        },
      },
      { status: 200 }
    )
  } catch (error: any) {
    return NextResponse.json(
      { detail: error.message },
      { status: 500 }
    )
  }
}
