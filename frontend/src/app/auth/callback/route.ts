import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

/**
 * OAuth Callback Route Handler
 * Handles OAuth redirect from Google/GitHub providers
 * Exchanges authorization code for session
 * Redirects to /dashboard on success or /login with error
 */
export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get('code');
  const error = requestUrl.searchParams.get('error');
  const errorDescription = requestUrl.searchParams.get('error_description');
  const origin = requestUrl.origin;

  // Handle OAuth error (user denied consent or provider error)
  if (error) {
    console.error('OAuth error:', error, errorDescription);
    return NextResponse.redirect(
      `${origin}/login?error=${encodeURIComponent(error)}&message=${encodeURIComponent(errorDescription || 'Authentication failed')}`
    );
  }

  // Code is required for OAuth flow
  if (!code) {
    return NextResponse.redirect(
      `${origin}/login?error=missing_code&message=${encodeURIComponent('Authorization code not provided')}`
    );
  }

  try {
    const cookieStore = await cookies();

    // Create Supabase server client with cookie handling
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() {
            return cookieStore.getAll();
          },
          setAll(cookiesToSet) {
            try {
              cookiesToSet.forEach(({ name, value, options }) =>
                cookieStore.set(name, value, options)
              );
            } catch (error) {
              // Handle cookie setting errors (can happen in middleware)
              console.error('Error setting cookies:', error);
            }
          },
        },
      }
    );

    // Exchange authorization code for session
    const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);

    if (exchangeError) {
      console.error('Code exchange error:', exchangeError);
      return NextResponse.redirect(
        `${origin}/login?error=invalid_code&message=${encodeURIComponent('Failed to authenticate. Please try again.')}`
      );
    }

    // Success - redirect to dashboard
    return NextResponse.redirect(`${origin}/dashboard`);
  } catch (err) {
    console.error('Unexpected error in OAuth callback:', err);
    return NextResponse.redirect(
      `${origin}/login?error=server_error&message=${encodeURIComponent('An unexpected error occurred')}`
    );
  }
}
