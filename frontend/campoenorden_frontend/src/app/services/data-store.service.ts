import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';

interface CacheEntry<T> {
  subject: Subject<T | null>;
  lastValue: T | null;
  hasEmitted: boolean;
  hasData: boolean;
  fetchedAt: number;
  inflight: boolean;
}

/**
 * Caché reactiva en memoria (stale-while-revalidate).
 * stream() emite el valor cacheado al instante y completa; si la clave es
 * nueva, no emite nada hasta el primer resultado real (completando con
 * take(1)), lo que mantiene compatible a consumidores de forkJoin y
 * evita flashes de estado vacío. Las escrituras invalidan las claves.
 */
@Injectable({ providedIn: 'root' })
export class DataStoreService {
  private cache = new Map<string, CacheEntry<any>>();
  private readonly DEFAULT_TTL = 60_000;

  stream<T>(
    key: string,
    fetcher: () => Observable<T>,
    ttlMs: number = this.DEFAULT_TTL,
    force = false
  ): Observable<T | null> {
    const isNew = !this.cache.has(key);
    const entry = isNew ? this.createEntry<T>() : this.cache.get(key)!;
    if (isNew) {
      this.cache.set(key, entry);
      this.fetch(entry, fetcher);
    } else if (force || Date.now() - entry.fetchedAt > ttlMs) {
      this.fetch(entry, fetcher);
    }
    return new Observable<T | null>((subscriber) => {
      if (entry.hasEmitted) {
        subscriber.next(entry.lastValue);
        subscriber.complete();
        return;
      }
      let settled = false;
      const subscription = entry.subject.subscribe({
        next: (value) => {
          subscriber.next(value);
          if (!settled) {
            settled = true;
            subscriber.complete();
          }
        },
        error: () => {
          if (!settled) {
            settled = true;
            subscriber.error(new Error('DataStore error'));
          }
        },
      });
      return () => subscription.unsubscribe();
    });
  }

  refresh<T>(key: string, fetcher: () => Observable<T>): void {
    const entry = this.cache.get(key);
    if (entry) {
      this.fetch(entry, fetcher);
    }
  }

  invalidate(key: string): void {
    this.cache.delete(key);
  }

  invalidatePrefix(prefix: string): void {
    for (const key of Array.from(this.cache.keys())) {
      if (key.startsWith(prefix)) {
        this.cache.delete(key);
      }
    }
  }

  invalidateAll(): void {
    this.cache.clear();
  }

  private createEntry<T>(): CacheEntry<T> {
    return {
      subject: new Subject<T | null>(),
      lastValue: null,
      hasEmitted: false,
      hasData: false,
      fetchedAt: 0,
      inflight: false,
    };
  }

  private emit<T>(entry: CacheEntry<T>, value: T | null): void {
    entry.hasEmitted = true;
    entry.lastValue = value;
    entry.subject.next(value);
  }

  private fetch<T>(entry: CacheEntry<T>, fetcher: () => Observable<T>): void {
    if (entry.inflight) return;
    entry.inflight = true;
    fetcher().subscribe({
      next: (value) => {
        entry.inflight = false;
        if (value === null || value === undefined) {
          if (!entry.hasData) {
            this.emit(entry, null);
          }
        } else {
          entry.hasData = true;
          entry.fetchedAt = Date.now();
          this.emit(entry, value);
        }
      },
      error: () => {
        entry.inflight = false;
        if (!entry.hasData) {
          this.emit(entry, null);
        }
      },
    });
  }
}