'use client'

import { Button } from '@/components/ui/button'

export function TopBar() {
  return (
    <header className="border-b bg-white">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold text-primary">
            Transfer2Read
          </h1>
        </div>
        <nav className="flex items-center gap-4">
          <Button variant="ghost">History</Button>
          <Button variant="ghost">Settings</Button>
        </nav>
      </div>
    </header>
  )
}
