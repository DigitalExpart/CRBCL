/**
 * CRBCL Secure Offline Web Workspace — Cryptographic Subsystem
 *
 * Implements browser-side application-level encryption for offline drafts using
 * the W3C Web Cryptography API (SubtleCrypto).
 *
 * Algorithm Specifications:
 * - Key Derivation: PBKDF2 (100,000 iterations, HMAC-SHA-256)
 * - Symmetric Cipher: AES-GCM (256-bit key length, 96-bit random IV per payload)
 * - Verifier: SHA-256 digest of derived key material (passphrase is never stored)
 */

let _activeSessionKey = null;

/**
 * Convert ArrayBuffer or Uint8Array to Base64 string
 */
function bufferToBase64(buffer) {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

/**
 * Convert Base64 string to Uint8Array
 */
function base64ToBuffer(base64) {
  const binary = window.atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

/**
 * Generate a cryptographically secure random 128-bit salt
 */
export function generateSalt() {
  const salt = new Uint8Array(16);
  window.crypto.getRandomValues(salt);
  return bufferToBase64(salt);
}

/**
 * Derive an AES-GCM 256-bit encryption key from a user passphrase and salt via PBKDF2
 */
export async function deriveKey(passphrase, saltBase64, iterations = 100000) {
  const enc = new TextEncoder();
  const passphraseBuffer = enc.encode(passphrase);
  const saltBuffer = base64ToBuffer(saltBase64);

  // Import passphrase as base key material
  const baseKey = await window.crypto.subtle.importKey(
    'raw',
    passphraseBuffer,
    { name: 'PBKDF2' },
    false,
    ['deriveKey', 'deriveBits']
  );

  // Derive AES-GCM 256-bit key
  const aesKey = await window.crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: saltBuffer,
      iterations: iterations,
      hash: 'SHA-256',
    },
    baseKey,
    { name: 'AES-GCM', length: 256 },
    true, // extractable for verifier hash computation
    ['encrypt', 'decrypt']
  );

  return aesKey;
}

/**
 * Compute SHA-256 verification hash of raw key bytes to confirm unlock passphrase
 */
export async function computeVerifier(cryptoKey) {
  const rawKey = await window.crypto.subtle.exportKey('raw', cryptoKey);
  const digest = await window.crypto.subtle.digest('SHA-256', rawKey);
  return bufferToBase64(digest);
}

/**
 * Encrypt arbitrary JSON object using AES-GCM
 */
export async function encryptData(dataObj, cryptoKey) {
  const effectiveKey = cryptoKey || _activeSessionKey;
  if (!effectiveKey) {
    throw new Error('OFFLINE_WORKSPACE_LOCKED: No active encryption key available.');
  }

  const enc = new TextEncoder();
  const plaintextBuffer = enc.encode(JSON.stringify(dataObj));

  // Generate 96-bit (12-byte) unique IV for AES-GCM
  const iv = new Uint8Array(12);
  window.crypto.getRandomValues(iv);

  const ciphertextBuffer = await window.crypto.subtle.encrypt(
    {
      name: 'AES-GCM',
      iv: iv,
    },
    effectiveKey,
    plaintextBuffer
  );

  return {
    iv: bufferToBase64(iv),
    ciphertext: bufferToBase64(ciphertextBuffer),
  };
}

/**
 * Decrypt AES-GCM payload and parse JSON object
 */
export async function decryptData(encryptedEnvelope, cryptoKey) {
  const effectiveKey = cryptoKey || _activeSessionKey;
  if (!effectiveKey) {
    throw new Error('OFFLINE_WORKSPACE_LOCKED: No active encryption key available.');
  }

  const ivBuffer = base64ToBuffer(encryptedEnvelope.iv);
  const ciphertextBuffer = base64ToBuffer(encryptedEnvelope.ciphertext);

  const decryptedBuffer = await window.crypto.subtle.decrypt(
    {
      name: 'AES-GCM',
      iv: ivBuffer,
    },
    effectiveKey,
    ciphertextBuffer
  );

  const dec = new TextDecoder();
  const jsonString = dec.decode(decryptedBuffer);
  return JSON.parse(jsonString);
}

/**
 * In-memory active session key management (strictly volatile in RAM)
 */
export function setSessionKey(cryptoKey) {
  _activeSessionKey = cryptoKey;
}

export function getSessionKey() {
  return _activeSessionKey;
}

export function clearSessionKey() {
  _activeSessionKey = null;
}

export function isSessionUnlocked() {
  return _activeSessionKey !== null;
}
