type CacheItem<T> = {
    data: T;
    timestamp: number;
    expiresAt: number;
  };
  
  export enum CacheDuration {
    SHORT = 30 * 1000, // 30 seconds
    MEDIUM = 5 * 60 * 1000, // 5 minutes
    LONG = 30 * 60 * 1000 // 30 minutes
  }
  
  class CacheService {
    private static instance: CacheService;
    private cache: Map<string, CacheItem<any>> = new Map();
    private subscribers: Map<string, Set<(data: any) => void>> = new Map();
  
    private constructor() {}
  
    static getInstance(): CacheService {
      if (!CacheService.instance) {
        CacheService.instance = new CacheService();
      }
      return CacheService.instance;
    }
  
    set<T>(key: string, data: T, duration: number): void {
      const now = Date.now();
      this.cache.set(key, {
        data,
        timestamp: now,
        expiresAt: now + duration
      });
      this.notifySubscribers(key, data);
    }
  
    get<T>(key: string): T | null {
      const item = this.cache.get(key);
      if (!item) return null;
  
      if (Date.now() > item.expiresAt) {
        this.cache.delete(key);
        return null;
      }
  
      return item.data as T;
    }
  
    subscribe<T>(key: string, callback: (data: T) => void): () => void {
      if (!this.subscribers.has(key)) {
        this.subscribers.set(key, new Set());
      }
      this.subscribers.get(key)!.add(callback);
  
      // Return unsubscribe function
      return () => {
        const subscribers = this.subscribers.get(key);
        if (subscribers) {
          subscribers.delete(callback);
          if (subscribers.size === 0) {
            this.subscribers.delete(key);
          }
        }
      };
    }
  
    private notifySubscribers(key: string, data: any): void {
      const subscribers = this.subscribers.get(key);
      if (subscribers) {
        subscribers.forEach(callback => callback(data));
      }
    }
  
    invalidate(key: string): void {
      this.cache.delete(key);
      this.notifySubscribers(key, null);
    }
  
    invalidatePattern(pattern: RegExp): void {
      for (const key of this.cache.keys()) {
        if (pattern.test(key)) {
          this.invalidate(key);
        }
      }
    }
  
    clear(): void {
      this.cache.clear();
      this.subscribers.clear();
    }
  }
  
  export const cacheService = CacheService.getInstance();
  