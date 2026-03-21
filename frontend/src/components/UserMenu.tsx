'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { UserResponse } from '@/types/contracts';
import { Button } from '@/components/ui/button';
import { User, LogOut } from 'lucide-react';

export function UserMenu() {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    api.getMe()
      .then(setUser)
      .catch(() => {
        api.logout();
        router.push('/login');
      });
  }, [router]);

  const handleLogout = () => {
    api.logout();
    router.push('/login');
  };

  if (!user) return null;

  return (
    <div className="relative">
      <Button 
        variant="ghost" 
        className="relative h-10 w-10 rounded-full bg-slate-100 flex items-center justify-center"
        onClick={() => setIsOpen(!isOpen)}
      >
        <User className="h-5 w-5 text-slate-600" />
      </Button>
      
      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
          <div className="py-1" role="menu" aria-orientation="vertical">
            <div className="px-4 py-3 border-b border-slate-100">
              <p className="text-sm font-medium text-slate-900">{user.name}</p>
              <p className="text-xs text-slate-500 truncate">{user.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="flex w-full items-center px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              role="menuitem"
            >
              <LogOut className="mr-3 h-4 w-4" />
              Cerrar sesión
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
