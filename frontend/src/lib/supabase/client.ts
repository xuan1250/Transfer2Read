import { createBrowserClient } from '@supabase/ssr';

/**
 * Supabase Client for Client Components
 * Use this in client components marked with 'use client'
 * @returns SupabaseClient configured for browser usage
 */
export const createClient = () => {
    return createBrowserClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );
};
