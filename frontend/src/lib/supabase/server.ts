import { createServerClient as createSupabaseServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

/**
 * Supabase Client for Server Components
 * Use this in server components for SSR operations
 * @returns SupabaseClient configured for server-side operations
 */
export const createServerClient = async () => {
    const cookieStore = await cookies();

    return createSupabaseServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                get(name: string) {
                    return cookieStore.get(name)?.value;
                },
                set(name: string, value: string, options: Record<string, unknown>) {
                    try {
                        cookieStore.set({ name, value, ...options });
                    } catch {
                        // Handle cookie setting errors
                    }
                },
                remove(name: string, options: Record<string, unknown>) {
                    try {
                        cookieStore.set({ name, value: '', ...options });
                    } catch {
                        // Handle cookie removal errors
                    }
                },
            },
        }
    );
};

/**
 * Supabase Client for API Route Handlers
 * Use this in Next.js API routes (app/api/*)
 * @returns SupabaseClient configured for route handler operations
 */
export const createRouteClient = async () => {
    const cookieStore = await cookies();

    return createSupabaseServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                get(name: string) {
                    return cookieStore.get(name)?.value;
                },
                set(name: string, value: string, options: Record<string, unknown>) {
                    try {
                        cookieStore.set({ name, value, ...options });
                    } catch {
                        // Handle cookie setting errors
                    }
                },
                remove(name: string, options: Record<string, unknown>) {
                    try {
                        cookieStore.set({ name, value: '', ...options });
                    } catch {
                        // Handle cookie removal errors
                    }
                },
            },
        }
    );
};
