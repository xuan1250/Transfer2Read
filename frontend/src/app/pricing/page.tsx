'use client';

import Link from 'next/link';
import { useUser } from '@/hooks/useUser';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function PricingPage() {
  const { user } = useUser();

  const tiers = [
    {
      name: 'Free',
      tier: 'FREE',
      price: '$0',
      frequency: '/month',
      description: 'Perfect for trying out Transfer2Read',
      features: [
        { name: '5 conversions per month', included: true },
        { name: 'Up to 50MB per file', included: true },
        { name: 'All conversion features', included: true },
        { name: 'Basic email support', included: true },
        { name: 'Priority processing', included: false },
        { name: 'Advanced features', included: false },
      ],
      cta: 'Sign Up',
      ctaLink: '/register',
      highlighted: false,
    },
    {
      name: 'Pro',
      tier: 'PRO',
      price: '$9',
      frequency: '/month',
      description: 'For regular users who need more conversions',
      features: [
        { name: 'Unlimited conversions', included: true },
        { name: 'No file size limit', included: true },
        { name: 'All conversion features', included: true },
        { name: 'Priority email support', included: true },
        { name: 'Priority processing', included: true },
        { name: 'Advanced features', included: false },
      ],
      cta: 'Coming Soon',
      ctaLink: '#',
      highlighted: true,
      badge: 'Most Popular',
    },
    {
      name: 'Premium',
      tier: 'PREMIUM',
      price: '$29',
      frequency: '/month',
      description: 'For power users and businesses',
      features: [
        { name: 'Unlimited conversions', included: true },
        { name: 'No file size limit', included: true },
        { name: 'All conversion features', included: true },
        { name: 'Dedicated support manager', included: true },
        { name: 'Priority processing', included: true },
        { name: 'Advanced features (coming soon)', included: true },
      ],
      cta: 'Coming Soon',
      ctaLink: '#',
      highlighted: false,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <header className="border-b bg-white">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="text-xl font-semibold text-primary hover:text-blue-700">
            Transfer2Read
          </Link>
          <div className="flex items-center gap-4">
            {user ? (
              <>
                <Link href="/dashboard">
                  <Button variant="ghost">Dashboard</Button>
                </Link>
                <Link href="/settings">
                  <Button variant="ghost">Settings</Button>
                </Link>
              </>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost">Sign In</Button>
                </Link>
                <Link href="/register">
                  <Button className="bg-blue-600 hover:bg-blue-700 text-white">Sign Up</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Pricing Content */}
      <div className="py-12 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">Simple, Transparent Pricing</h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Choose the plan that fits your needs. Upgrade or downgrade at any time.
            </p>
          </div>

          {/* Pricing Tiers */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {tiers.map((tier) => (
              <Card
                key={tier.tier}
                className={`relative ${
                  tier.highlighted
                    ? 'border-blue-500 border-2 shadow-lg scale-105'
                    : 'border-gray-200'
                }`}
              >
                {tier.badge && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-blue-500 text-white text-xs font-semibold px-3 py-1 rounded-full">
                      {tier.badge}
                    </span>
                  </div>
                )}

                <CardHeader className="text-center pb-8 pt-6">
                  <CardTitle className="text-2xl font-bold text-gray-900">{tier.name}</CardTitle>
                  <CardDescription className="mt-2">{tier.description}</CardDescription>
                  <div className="mt-6">
                    <span className="text-5xl font-bold text-gray-900">{tier.price}</span>
                    <span className="text-gray-600">{tier.frequency}</span>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <ul className="space-y-3">
                    {tier.features.map((feature, index) => (
                      <li key={index} className="flex items-start gap-3">
                        {feature.included ? (
                          <svg
                            className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5"
                            fill="none"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path d="M5 13l4 4L19 7"></path>
                          </svg>
                        ) : (
                          <svg
                            className="h-5 w-5 text-gray-300 flex-shrink-0 mt-0.5"
                            fill="none"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path d="M6 18L18 6M6 6l12 12"></path>
                          </svg>
                        )}
                        <span
                          className={`text-sm ${
                            feature.included ? 'text-gray-700' : 'text-gray-400'
                          }`}
                        >
                          {feature.name}
                        </span>
                      </li>
                    ))}
                  </ul>
                </CardContent>

                <CardFooter className="pt-6">
                  {tier.tier === 'FREE' ? (
                    <Link href={tier.ctaLink} className="w-full">
                      <Button
                        className={`w-full ${
                          tier.highlighted
                            ? 'bg-blue-600 hover:bg-blue-700 text-white'
                            : 'bg-gray-100 hover:bg-gray-200 text-gray-900'
                        }`}
                      >
                        {tier.cta}
                      </Button>
                    </Link>
                  ) : (
                    <Button
                      disabled
                      className={`w-full ${
                        tier.highlighted
                          ? 'bg-blue-600 hover:bg-blue-700 text-white'
                          : 'bg-gray-100 hover:bg-gray-200 text-gray-900'
                      } opacity-50 cursor-not-allowed`}
                    >
                      {tier.cta}
                    </Button>
                  )}
                </CardFooter>
              </Card>
            ))}
          </div>

          {/* Payment Notice */}
          <div className="mt-12 text-center">
            <div className="bg-blue-50 border border-blue-200 text-blue-800 px-6 py-4 rounded-lg inline-block max-w-2xl">
              <p className="text-sm font-medium">
                💳 Payment integration coming soon!
              </p>
              <p className="text-sm mt-2">
                Stripe integration for Pro and Premium plans will be available in Epic 6.
                Sign up for Free to start converting your PDFs today.
              </p>
            </div>
          </div>

          {/* FAQ or Additional Info (Optional) */}
          <div className="mt-16 max-w-3xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-900 text-center mb-6">
              Frequently Asked Questions
            </h2>
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Can I upgrade or downgrade my plan?</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">
                    Yes! You can upgrade or downgrade your plan at any time. Changes will be reflected
                    immediately, and billing will be prorated.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">What happens if I exceed my conversion limit?</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">
                    For Free tier users, you&apos;ll need to upgrade to Pro or Premium to continue converting.
                    Pro and Premium users have unlimited conversions.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Is there a free trial for Pro or Premium?</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">
                    The Free plan lets you try all conversion features with 5 conversions per month.
                    This is essentially a perpetual free tier - no credit card required.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
