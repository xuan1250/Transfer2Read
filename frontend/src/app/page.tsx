'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      setIsAuthenticated(!!session);
    };
    checkAuth();
  }, []);

  const handleGetStarted = () => {
    if (isAuthenticated) {
      router.push('/upload');
    } else {
      router.push('/login');
    }
  };

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-4xl mx-auto text-center space-y-8">
        <div className="space-y-4">
          <h1 className="text-4xl font-bold text-foreground">
            Convert Complex PDFs to Beautiful EPUBs
          </h1>
          <p className="text-xl text-muted-foreground">
            AI-powered layout analysis for technical and academic documents
          </p>
        </div>

        <div className="flex justify-center gap-4">
          <Button size="lg" onClick={handleGetStarted}>
            Get Started
          </Button>
          <Button size="lg" variant="outline" onClick={() => router.push('/pricing')}>
            Learn More
          </Button>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mt-16">
          <Card>
            <CardHeader>
              <CardTitle>AI-Powered Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Advanced AI analyzes document structure, preserving complex layouts and formatting
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Fast Conversion</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Optimized processing pipeline delivers high-quality EPUBs in minutes
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quality Preview</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Review side-by-side comparison before downloading your converted document
              </CardDescription>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
