import { create } from 'zustand'
import { generateId } from '@/lib/utils'

/* ═══════════════════════════════════════
   DEMO DATA
   ═══════════════════════════════════════ */

const DEMO_ORDERS = [
  { id: '1', customer: 'Marco Rossi', customerAvatar: null, items: 'Drago giapponese — avambraccio destro', quantity: 1, total: 350, status: 'In corso', priority: 'high', date: '2026-03-15', channel: 'instagram', notes: 'Dettagli rosso e nero, stile realistico' },
  { id: '2', customer: 'Giulia Bianchi', customerAvatar: null, items: 'Portafoglio in pelle personalizzato', quantity: 2, total: 180, status: 'Confermato', priority: 'medium', date: '2026-03-18', channel: 'whatsapp', notes: 'Incisione iniziali G.B.' },
  { id: '3', customer: 'Alessandro Conti', customerAvatar: null, items: 'Ritratto famiglia — schiena', quantity: 1, total: 600, status: 'Bozzetto', priority: 'high', date: '2026-03-20', channel: 'instagram', notes: 'Foto di riferimento ricevute' },
  { id: '4', customer: 'Sara Lombardi', customerAvatar: null, items: 'Minimal rose — polso', quantity: 1, total: 120, status: 'Completato', priority: 'low', date: '2026-03-10', channel: 'whatsapp', notes: '' },
  { id: '5', customer: 'Luca Ferrari', customerAvatar: null, items: 'Cover-up tribale', quantity: 1, total: 450, status: 'Richiesta', priority: 'medium', date: '2026-03-22', channel: 'facebook', notes: 'Vuole coprire vecchio tattoo tribale sulla spalla' },
  { id: '6', customer: 'Elena Moretti', customerAvatar: null, items: 'Scritta corsivo — costato', quantity: 1, total: 200, status: 'Approvato', priority: 'medium', date: '2026-03-16', channel: 'instagram', notes: 'Frase in latino' },
  { id: '7', customer: 'Francesco Russo', customerAvatar: null, items: 'Manica completa old school', quantity: 1, total: 1200, status: 'In corso', priority: 'high', date: '2026-03-25', channel: 'whatsapp', notes: 'Terza sessione, mancano ancora 2' },
  { id: '8', customer: 'Chiara Esposito', customerAvatar: null, items: 'Farfalla watercolor — scapola', quantity: 1, total: 280, status: 'Completato', priority: 'low', date: '2026-03-08', channel: 'instagram', notes: 'Cliente molto soddisfatta' },
]

const DEMO_INVENTORY = [
  { id: '1', name: 'Inchiostro nero Dynamic', category: 'Inchiostri', quantity: 12, minQuantity: 5, unit: 'bottiglie', price: 18.5, supplier: 'TattooSupply IT' },
  { id: '2', name: 'Aghi RL 3', category: 'Aghi', quantity: 45, minQuantity: 20, unit: 'pz', price: 0.8, supplier: 'NeedlePro' },
  { id: '3', name: 'Aghi RS 7', category: 'Aghi', quantity: 8, minQuantity: 20, unit: 'pz', price: 0.95, supplier: 'NeedlePro' },
  { id: '4', name: 'Pellicola protettiva', category: 'Medicazione', quantity: 3, minQuantity: 10, unit: 'rotoli', price: 22, supplier: 'MedSupply' },
  { id: '5', name: 'Inchiostro rosso Eternal', category: 'Inchiostri', quantity: 6, minQuantity: 3, unit: 'bottiglie', price: 22, supplier: 'TattooSupply IT' },
  { id: '6', name: 'Guanti nitrile M', category: 'Protezione', quantity: 150, minQuantity: 50, unit: 'pz', price: 0.12, supplier: 'MedSupply' },
  { id: '7', name: 'Carta transfer', category: 'Trasferimento', quantity: 28, minQuantity: 15, unit: 'fogli', price: 0.5, supplier: 'TattooSupply IT' },
  { id: '8', name: 'Crema Bepanthenol', category: 'Aftercare', quantity: 18, minQuantity: 10, unit: 'tubetti', price: 8.5, supplier: 'Farmacia Centrale' },
]

const DEMO_EVENTS = [
  { id: '1', title: 'Marco Rossi — Sessione 2', date: '2026-03-12', time: '10:00', duration: 180, type: 'appointment', color: 'blue', contactId: '1' },
  { id: '2', title: 'Giulia Bianchi — Consultazione', date: '2026-03-12', time: '15:00', duration: 30, type: 'appointment', color: 'green', contactId: '2' },
  { id: '3', title: 'Ordine aghi — scadenza', date: '2026-03-13', time: '09:00', duration: 0, type: 'deadline', color: 'red' },
  { id: '4', title: 'Alessandro Conti — Revisione bozzetto', date: '2026-03-14', time: '11:00', duration: 60, type: 'appointment', color: 'purple', contactId: '3' },
  { id: '5', title: 'Convention tattoo Roma', date: '2026-03-20', time: '09:00', duration: 480, type: 'event', color: 'orange' },
  { id: '6', title: 'Elena Moretti — Sessione', date: '2026-03-16', time: '14:00', duration: 120, type: 'appointment', color: 'blue', contactId: '6' },
]

const DEMO_CONTACTS = [
  { id: '1', name: 'Marco Rossi', email: 'marco.rossi@email.com', phone: '+39 333 1234567', channel: 'instagram', handle: '@marcorossi', totalSpent: 700, ordersCount: 3, lastVisit: '2026-03-10', tags: ['VIP', 'Fedele'], notes: 'Preferisce stile realistico' },
  { id: '2', name: 'Giulia Bianchi', email: 'giulia.b@email.com', phone: '+39 340 9876543', channel: 'whatsapp', handle: null, totalSpent: 180, ordersCount: 1, lastVisit: '2026-03-08', tags: ['Nuovo'], notes: '' },
  { id: '3', name: 'Alessandro Conti', email: 'ale.conti@email.com', phone: '+39 347 5551234', channel: 'instagram', handle: '@ale_conti', totalSpent: 1200, ordersCount: 4, lastVisit: '2026-03-05', tags: ['VIP', 'Fedele'], notes: 'Cliente da 2 anni, sempre puntuale' },
  { id: '4', name: 'Sara Lombardi', email: 'sara.l@email.com', phone: '+39 320 4443333', channel: 'whatsapp', handle: null, totalSpent: 120, ordersCount: 1, lastVisit: '2026-03-10', tags: [], notes: '' },
  { id: '5', name: 'Luca Ferrari', email: 'luca.ferrari@email.com', phone: '+39 388 7776666', channel: 'facebook', handle: null, totalSpent: 0, ordersCount: 0, lastVisit: null, tags: ['Prospect'], notes: 'Primo contatto, vuole info cover-up' },
  { id: '6', name: 'Elena Moretti', email: 'elena.m@email.com', phone: '+39 331 2221111', channel: 'instagram', handle: '@elena_moretti', totalSpent: 200, ordersCount: 1, lastVisit: '2026-03-07', tags: [], notes: 'Frase in latino approvata' },
  { id: '7', name: 'Francesco Russo', email: 'f.russo@email.com', phone: '+39 345 8889999', channel: 'whatsapp', handle: null, totalSpent: 2400, ordersCount: 5, lastVisit: '2026-03-11', tags: ['VIP', 'Fedele', 'Top Spender'], notes: 'Progetto manica completa in corso' },
  { id: '8', name: 'Chiara Esposito', email: 'chiara.e@email.com', phone: '+39 339 6665544', channel: 'instagram', handle: '@chiara.esp', totalSpent: 280, ordersCount: 1, lastVisit: '2026-03-08', tags: [], notes: 'Molto contenta del risultato' },
]

const DEMO_CONVERSATIONS = [
  {
    id: '1', contactId: '1', contactName: 'Marco Rossi', contactAvatar: null, channel: 'instagram',
    lastMessage: 'Perfetto, ci vediamo domani alle 10!', lastMessageTime: '2026-03-11T18:30:00', unread: false,
    messages: [
      { id: 'm1', text: 'Ciao! Volevo sapere se possiamo anticipare la sessione di domani', sender: 'customer', timestamp: '2026-03-11T17:00:00' },
      { id: 'm2', text: 'Ciao Marco! Purtroppo domani mattina ho già un appuntamento. Possiamo fare alle 10 come previsto?', sender: 'business', timestamp: '2026-03-11T17:15:00' },
      { id: 'm3', text: 'Perfetto, ci vediamo domani alle 10!', sender: 'customer', timestamp: '2026-03-11T18:30:00' },
    ],
  },
  {
    id: '2', contactId: '5', contactName: 'Luca Ferrari', contactAvatar: null, channel: 'facebook',
    lastMessage: 'Vorrei un preventivo per un cover-up sulla spalla', lastMessageTime: '2026-03-11T20:00:00', unread: true,
    messages: [
      { id: 'm1', text: 'Buonasera! Ho visto i vostri lavori su Instagram e sono interessato', sender: 'customer', timestamp: '2026-03-11T19:30:00' },
      { id: 'm2', text: 'Vorrei un preventivo per un cover-up sulla spalla', sender: 'customer', timestamp: '2026-03-11T20:00:00' },
    ],
  },
  {
    id: '3', contactId: '3', contactName: 'Alessandro Conti', contactAvatar: null, channel: 'instagram',
    lastMessage: 'Ti mando le foto di riferimento per il ritratto', lastMessageTime: '2026-03-10T14:20:00', unread: true,
    messages: [
      { id: 'm1', text: 'Ciao! Come procede il bozzetto?', sender: 'customer', timestamp: '2026-03-10T10:00:00' },
      { id: 'm2', text: 'Ciao Ale! Sto ancora lavorando sui dettagli. Dovresti mandarmi le foto in alta risoluzione', sender: 'business', timestamp: '2026-03-10T11:30:00' },
      { id: 'm3', text: 'Ti mando le foto di riferimento per il ritratto', sender: 'customer', timestamp: '2026-03-10T14:20:00' },
    ],
  },
  {
    id: '4', contactId: '8', contactName: 'Chiara Esposito', contactAvatar: null, channel: 'instagram',
    lastMessage: 'Grazie mille! Sono super contenta del risultato ❤️', lastMessageTime: '2026-03-08T19:00:00', unread: false,
    messages: [
      { id: 'm1', text: 'Come sta guarendo il tattoo?', sender: 'business', timestamp: '2026-03-08T16:00:00' },
      { id: 'm2', text: 'Benissimo! Si vede già benissimo', sender: 'customer', timestamp: '2026-03-08T17:30:00' },
      { id: 'm3', text: 'Grazie mille! Sono super contenta del risultato ❤️', sender: 'customer', timestamp: '2026-03-08T19:00:00' },
    ],
  },
]

const DEMO_NOTIFICATIONS = [
  { id: '1', type: 'order', title: 'Nuovo ordine', message: 'Luca Ferrari ha richiesto un cover-up', time: '2026-03-11T20:00:00', read: false },
  { id: '2', type: 'inventory', title: 'Scorte in esaurimento', message: 'Aghi RS 7: solo 8 pezzi rimasti', time: '2026-03-11T09:00:00', read: false },
  { id: '3', type: 'inventory', title: 'Scorte in esaurimento', message: 'Pellicola protettiva: solo 3 rotoli rimasti', time: '2026-03-11T09:00:00', read: false },
  { id: '4', type: 'calendar', title: 'Appuntamento domani', message: 'Marco Rossi — Sessione 2 alle 10:00', time: '2026-03-11T21:00:00', read: true },
  { id: '5', type: 'chat', title: 'Nuovo messaggio', message: 'Alessandro Conti ti ha scritto su Instagram', time: '2026-03-10T14:20:00', read: true },
  { id: '6', type: 'payment', title: 'Pagamento ricevuto', message: 'Sara Lombardi ha pagato €120', time: '2026-03-10T16:00:00', read: true },
]

/* ═══════════════════════════════════════
   Unified App Store — Orders, Inventory,
   Calendar, Contacts, Chat, Notifications
   ═══════════════════════════════════════ */

const useAppStore = create((set, get) => ({
  /* ── Orders ── */
  orders: DEMO_ORDERS,
  orderFilter: 'all',

  addOrder: (order) =>
    set((s) => ({ orders: [{ id: generateId(), createdAt: new Date().toISOString(), ...order }, ...s.orders] })),

  updateOrder: (id, data) =>
    set((s) => ({ orders: s.orders.map((o) => (o.id === id ? { ...o, ...data } : o)) })),

  deleteOrder: (id) =>
    set((s) => ({ orders: s.orders.filter((o) => o.id !== id) })),

  setOrderFilter: (filter) => set({ orderFilter: filter }),

  getFilteredOrders: () => {
    const { orders, orderFilter } = get()
    if (orderFilter === 'all') return orders
    return orders.filter((o) => o.status === orderFilter)
  },

  /* ── Inventory ── */
  inventory: DEMO_INVENTORY,

  addItem: (item) =>
    set((s) => ({ inventory: [{ id: generateId(), ...item }, ...s.inventory] })),

  updateItem: (id, data) =>
    set((s) => ({ inventory: s.inventory.map((i) => (i.id === id ? { ...i, ...data } : i)) })),

  deleteItem: (id) =>
    set((s) => ({ inventory: s.inventory.filter((i) => i.id !== id) })),

  getLowStockItems: () => get().inventory.filter((i) => i.quantity <= i.minQuantity),

  /* ── Calendar Events ── */
  events: DEMO_EVENTS,

  addEvent: (event) =>
    set((s) => ({ events: [...s.events, { id: generateId(), ...event }] })),

  updateEvent: (id, data) =>
    set((s) => ({ events: s.events.map((e) => (e.id === id ? { ...e, ...data } : e)) })),

  deleteEvent: (id) =>
    set((s) => ({ events: s.events.filter((e) => e.id !== id) })),

  getTodayEvents: () => {
    const today = new Date().toISOString().split('T')[0]
    return get().events.filter((e) => e.date === today)
  },

  /* ── Contacts ── */
  contacts: DEMO_CONTACTS,

  addContact: (contact) =>
    set((s) => ({ contacts: [{ id: generateId(), createdAt: new Date().toISOString(), ...contact }, ...s.contacts] })),

  updateContact: (id, data) =>
    set((s) => ({ contacts: s.contacts.map((c) => (c.id === id ? { ...c, ...data } : c)) })),

  deleteContact: (id) =>
    set((s) => ({ contacts: s.contacts.filter((c) => c.id !== id) })),

  /* ── Chat Conversations ── */
  conversations: DEMO_CONVERSATIONS,
  activeConversation: null,

  setActiveConversation: (id) => set({ activeConversation: id }),

  addMessage: (conversationId, message) =>
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === conversationId
          ? {
              ...c,
              messages: [...c.messages, { id: generateId(), timestamp: new Date().toISOString(), ...message }],
              lastMessage: message.text,
              lastMessageTime: new Date().toISOString(),
              unread: false,
            }
          : c
      ),
    })),

  getUnreadCount: () => get().conversations.filter((c) => c.unread).length,

  /* ── Notifications ── */
  notifications: DEMO_NOTIFICATIONS,

  addNotification: (notif) =>
    set((s) => ({ notifications: [{ id: generateId(), time: new Date().toISOString(), read: false, ...notif }, ...s.notifications] })),

  markNotificationRead: (id) =>
    set((s) => ({ notifications: s.notifications.map((n) => (n.id === id ? { ...n, read: true } : n)) })),

  markAllNotificationsRead: () =>
    set((s) => ({ notifications: s.notifications.map((n) => ({ ...n, read: true })) })),

  getUnreadNotifications: () => get().notifications.filter((n) => !n.read),

  /* ── Search ── */
  globalSearch: '',
  setGlobalSearch: (q) => set({ globalSearch: q }),
}))

export default useAppStore
