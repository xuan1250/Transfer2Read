'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useUser } from '@/hooks/useUser';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, Sparkles, X } from 'lucide-react';
import { SubscriptionTier } from '@/types/usage';
import { useToast } from '@/hooks/use-toast';

export default function PricingPage() {
  const { user } = useUser();
  const router = useRouter();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const currentTier: SubscriptionTier = (user?.user_metadata?.tier as SubscriptionTier) || 'FREE';

  const handleSelectPlan = async (tier: SubscriptionTier) => {
    // If user is already on this tier
    if (tier === currentTier) {
      toast({
        title: 'Already subscribed',
        description: `You're already on the ${tier} plan.`,
        variant: 'default',
      });
      return;
    }

    // If selecting FREE tier (downgrade)
    if (tier === 'FREE') {
      toast({
        title: 'Contact support',
        description: 'To downgrade your plan, please contact our support team.',
      });
      return;
    }

    // For PRO/PREMIUM: Show placeholder (MVP) or redirect to Stripe (full integration)
    setIsLoading(true);

    // MVP Placeholder approach
    toast({
      title: 'Payment integration coming soon!',
      description: 'Please contact support@transfer2read.com to upgrade your account.',
      duration: 5000,
    });
    setIsLoading(false);

    // TODO: Full Stripe integration (Story 6.3 - Option B)
    // const response = await fetch('/api/v1/checkout/create-session', {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json',
    //     Authorization: `Bearer ${session.access_token}`,
    //   },
    //   body: JSON.stringify({ tier }),
    // });
    // const { checkout_url } = await response.json();
    // window.location.href = checkout_url;
  };

  const tiers = [
    {
      name: 'Free',
      tier: 'FREE' as SubscriptionTier,
      price: 0,
      frequency: '/month',
      description: 'Perfect for trying out Transfer2Read',
      features: [
        '5 conversions per month',
        '50MB maximum file size',
        'Basic PDF to EPUB conversion',
        'Community support',
        'Standard processing speed',
      ],
      cta: 'Sign Up',
      highlighted: false,
    },
    {
      name: 'Pro',
      tier: 'PRO' as SubscriptionTier,
      price: 9.99,
      frequency: '/month',
      description: 'For regular users who need more conversions',
      features: [
        'Unlimited conversions',
        'Unlimited file size',
        'Advanced AI analysis',
        'Priority email support',
        'Faster processing speed',
        'Download history archive',
      ],
      cta: 'Upgrade to Pro',
      highlighted: true,
      badge: 'Recommended',
    },
    {
      name: 'Premium',
      tier: 'PREMIUM' as SubscriptionTier,
      price: 19.99,
      frequency: '/month',
      description: 'For power users and businesses',
      features: [
        'Everything in Pro',
        'Batch conversion (coming soon)',
        'API access (coming soon)',
        'Custom AI training (coming soon)',
        'Priority 24/7 support',
        'Advanced customization',
        'Dedicated account manager',
      ],
      cta: 'Upgrade to Premium',
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
            {tiers.map((tierData) => {
              const isCurrent = tierData.tier === currentTier;
              const isRecommended = tierData.highlighted;

              return (
                <Card
                  key={tierData.tier}
                  className={`relative flex flex-col ${
                    isRecommended
                      ? 'border-blue-600 border-2 shadow-xl scale-105'
                      : 'border-gray-200'
                  }`}
                >
                  {/* Recommended Badge */}
                  {isRecommended && tierData.badge && (
                    <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                      <Badge className="bg-blue-600 hover:bg-blue-700 px-4 py-1 gap-1">
                        <Sparkles className="h-3 w-3" />
                        {tierData.badge}
                      </Badge>
                    </div>
                  )}

                  <CardHeader className="text-center pb-8 pt-8">
                    <CardTitle className="text-2xl font-bold mb-2">
                      {tierData.name}
                    </CardTitle>
                    <CardDescription className="mt-2">{tierData.description}</CardDescription>
                    <div className="mt-6">
                      {tierData.price > 0 ? (
                        <div className="flex items-baseline justify-center gap-1">
                          <span className="text-4xl font-bold text-blue-600">
                            ${tierData.price}
                          </span>
                          <span className="text-gray-600">{tierData.frequency}</span>
                        </div>
                      ) : (
                        <div className="text-3xl font-bold text-gray-900">Free</div>
                      )}
                    </div>
                    {isCurrent && (
                      <Badge variant="outline" className="mt-3">
                        Current Plan
                      </Badge>
                    )}
                  </CardHeader>

                  <CardContent className="flex-grow">
                    <ul className="space-y-3">
                      {tierData.features.map((feature, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <Check className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
                          <span className="text-sm text-gray-700">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>

                  <CardFooter className="pt-6">
                    <Button
                      onClick={() => handleSelectPlan(tierData.tier)}
                      disabled={isCurrent || isLoading}
                      className={`w-full ${
                        isRecommended
                          ? 'bg-blue-600 hover:bg-blue-700 text-white'
                          : 'bg-gray-900 hover:bg-gray-800 text-white'
                      }`}
                      variant={isCurrent ? 'outline' : 'default'}
                    >
                      {isCurrent ? 'Current Plan' : tierData.cta}
                    </Button>
                  </CardFooter>
                </Card>
              );
            })}
          </div>

          {/* FAQ or Additional Info */}
          <div className="mt-16 max-w-3xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-900 text-center mb-6">
              Frequently Asked Questions
            </h2>
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Can I change my plan later?</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">
                    Yes! You can upgrade or downgrade your plan at any time. Upgrades take effect immediately,
                    while downgrades will apply at the end of your current billing cycle.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">What payment methods do you accept?</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">
                    We accept all major credit cards (Visa, Mastercard, American Express) through our secure
                    payment processor Stripe. Support for PayPal coming soon.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">What happens when I hit my monthly limit?</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">
                    On the Free tier, you'll be notified when you reach your 5 conversions/month limit.
                    You can upgrade to Pro for unlimited conversions anytime, or wait until next month when
                    your limit resets.
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Is there a refund policy?</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">
                    Yes! We offer a 30-day money-back guarantee. If you're not satisfied with Pro or Premium,
                    contact us within 30 days for a full refund.
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
