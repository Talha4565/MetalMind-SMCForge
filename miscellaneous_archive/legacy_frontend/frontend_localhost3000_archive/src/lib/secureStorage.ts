import CryptoJS from 'crypto-js';

const ENCRYPTION_KEY = import.meta.env.VITE_STORAGE_KEY || 'default-key-change-in-production';

/**
 * Secure storage wrapper with encryption
 * Uses crypto-js for AES encryption
 */
class SecureStorage {
  private encrypt(data: string): string {
    try {
      return CryptoJS.AES.encrypt(data, ENCRYPTION_KEY).toString();
    } catch (error) {
      console.error('Encryption error:', error);
      throw new Error('Failed to encrypt data');
    }
  }

  private decrypt(ciphertext: string): string {
    try {
      const bytes = CryptoJS.AES.decrypt(ciphertext, ENCRYPTION_KEY);
      const decrypted = bytes.toString(CryptoJS.enc.Utf8);
      if (!decrypted) {
        throw new Error('Decryption failed');
      }
      return decrypted;
    } catch (error) {
      console.error('Decryption error:', error);
      throw new Error('Failed to decrypt data');
    }
  }

  setItem(key: string, value: string): void {
    try {
      const encrypted = this.encrypt(value);
      localStorage.setItem(key, encrypted);
    } catch (error) {
      console.error('SecureStorage.setItem error:', error);
      throw error;
    }
  }

  getItem(key: string): string | null {
    try {
      const encrypted = localStorage.getItem(key);
      if (!encrypted) {
        return null;
      }
      return this.decrypt(encrypted);
    } catch (error) {
      console.error('SecureStorage.getItem error:', error);
      // If decryption fails, remove corrupted data
      this.removeItem(key);
      return null;
    }
  }

  removeItem(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('SecureStorage.removeItem error:', error);
    }
  }

  clear(): void {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('SecureStorage.clear error:', error);
    }
  }

  // Store JSON objects
  setObject<T>(key: string, value: T): void {
    try {
      const json = JSON.stringify(value);
      this.setItem(key, json);
    } catch (error) {
      console.error('SecureStorage.setObject error:', error);
      throw error;
    }
  }

  // Retrieve JSON objects
  getObject<T>(key: string): T | null {
    try {
      const json = this.getItem(key);
      if (!json) {
        return null;
      }
      return JSON.parse(json) as T;
    } catch (error) {
      console.error('SecureStorage.getObject error:', error);
      return null;
    }
  }

  // Check if key exists
  hasItem(key: string): boolean {
    return this.getItem(key) !== null;
  }
}

export const secureStorage = new SecureStorage();
