import {
  LayoutDashboard, ShoppingCart, Package, CalendarDays,
  MessageCircle, Users, BarChart3, Settings, HelpCircle,
  Sparkles,
} from 'lucide-react'

export const NAVIGATION_ITEMS = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    path: '/',
    group: 'main',
  },
  {
    id: 'orders',
    label: 'Ordini',
    terminologyKey: 'orders',
    icon: ShoppingCart,
    path: '/orders',
    group: 'main',
    badge: 'orderCount',
  },
  {
    id: 'inventory',
    label: 'Magazzino',
    terminologyKey: 'inventory',
    icon: Package,
    path: '/inventory',
    group: 'main',
    badge: 'lowStockCount',
  },
  {
    id: 'calendar',
    label: 'Calendario',
    terminologyKey: 'calendar',
    icon: CalendarDays,
    path: '/calendar',
    group: 'main',
    badge: 'todayEvents',
  },
  {
    id: 'chat',
    label: 'Chat',
    icon: MessageCircle,
    path: '/chat',
    group: 'main',
    badge: 'unreadMessages',
  },
  {
    id: 'contacts',
    label: 'Contatti',
    terminologyKey: 'contacts',
    icon: Users,
    path: '/contacts',
    group: 'main',
  },
  {
    id: 'analytics',
    label: 'Statistiche',
    icon: BarChart3,
    path: '/analytics',
    group: 'secondary',
  },
  {
    id: 'ai',
    label: 'Mercurio AI',
    icon: Sparkles,
    path: '/ai',
    group: 'secondary',
    premium: true,
  },
  {
    id: 'settings',
    label: 'Impostazioni',
    icon: Settings,
    path: '/settings',
    group: 'footer',
  },
  {
    id: 'help',
    label: 'Aiuto',
    icon: HelpCircle,
    path: '/help',
    group: 'footer',
  },
]

export function getNavItems(group) {
  return NAVIGATION_ITEMS.filter((item) => item.group === group)
}
