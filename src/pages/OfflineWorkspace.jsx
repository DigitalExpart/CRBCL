import React, { useState, useEffect, useCallback } from 'react';
import { 
  Wifi, WifiOff, RefreshCw, Lock, Unlock, ShieldAlert, 
  UserPlus, FileInput, FileText, CheckCircle2, AlertTriangle, 
  Clock, XCircle, Trash2, Eye, ShieldCheck, Database, KeyRound
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/context/AuthContext';

import { 
  deriveKey, computeVerifier, generateSalt, 
  encryptData, decryptData, setSessionKey, 
  getSessionKey, clearSessionKey, isSessionUnlocked 
} from '@/lib/offline-crypto';
import { OfflineDB } from '@/lib/offline-db';
import { OfflineSyncEngine } from '@/lib/offline-sync';

export default function OfflineWorkspace() {
  const { user } = useAuth();
  const { toast } = useToast();

  const userId = user?.id || 'anonymous_caseworker';
  const userName = user?.display_name || user?.name || user?.email || 'Caseworker';

  // System states
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isBackendReachable, setIsBackendReachable] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isUnlocked, setIsUnlocked] = useState(isSessionUnlocked());
  const [isEnrolled, setIsEnrolled] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState(null);

  // Auth / Unlock modal states
  const [passphrase, setPassphrase] = useState('');
  const [confirmPassphrase, setConfirmPassphrase] = useState('');
  const [unlockError, setUnlockError] = useState('');
  const [isUnlockModalOpen, setIsUnlockModalOpen] = useState(false);

  // Drafts & metrics
  const [drafts, setDrafts] = useState([]);
  const [metrics, setMetrics] = useState({
    TOTAL: 0,
    WAITING_TO_SYNC: 0,
    SYNCED: 0,
    NEEDS_REVIEW: 0,
    FAILED: 0,
  });
  const [activeFilter, setActiveFilter] = useState('ALL');

  // Modals for creating drafts
  const [activeModal, setActiveModal] = useState(null); // 'CLIENT' | 'INTAKE' | 'CASE_NOTE' | 'VIEW'
  const [selectedDraft, setSelectedDraft] = useState(null);
  const [decryptedViewData, setDecryptedViewData] = useState(null);

  // Form states
  const [clientForm, setClientForm] = useState({
    firstName: '',
    lastName: '',
    dateOfBirth: '',
    gender: 'Prefer not to say',
    phone: '',
    email: '',
    address: '',
    city: 'Kamsack',
    province: 'Saskatchewan',
    treatyNumber: '',
    bandNation: 'Cote First Nation',
    indigenousIdentity: 'Status First Nation',
    status: 'Pending Intake',
    riskLevel: 'Low',
    notes: '',
  });

  const [intakeForm, setIntakeForm] = useState({
    summary: '',
    receivedDate: new Date().toISOString().split('T')[0],
    receivedTime: '10:00',
    receivedMethod: 'In Person',
    community: 'Cote First Nation',
    priority: 'Medium',
    riskLevel: 'Low',
    immediateSafetyConcerns: false,
    lawEnforcementInvolved: false,
    notes: '',
  });

  const [noteForm, setNoteForm] = useState({
    caseNumber: '',
    title: '',
    noteType: 'Progress Note',
    summary: '',
    contactType: 'In Person',
    durationMinutes: '30',
  });

  // Check enrollment status and load metrics
  const loadWorkspaceState = useCallback(async () => {
    try {
      const authMeta = await OfflineDB.getAuthMetadata(userId);
      setIsEnrolled(Boolean(authMeta?.verifierHash));

      if (isSessionUnlocked()) {
        setIsUnlocked(true);
        const userDrafts = await OfflineDB.getDrafts(userId, activeFilter);
        setDrafts(userDrafts);
        const userMetrics = await OfflineDB.getMetrics(userId);
        setMetrics(userMetrics);
      } else {
        setIsUnlocked(false);
      }
    } catch (err) {
      console.error('Failed to load offline workspace state:', err);
    }
  }, [userId, activeFilter]);

  // Connectivity monitoring
  const checkConnection = useCallback(async () => {
    const conn = await OfflineSyncEngine.checkConnectivity();
    setIsOnline(conn.isOnline);
    setIsBackendReachable(conn.isBackendReachable);
  }, []);

  useEffect(() => {
    checkConnection();
    loadWorkspaceState();

    const handleOnline = () => checkConnection();
    const handleOffline = () => {
      setIsOnline(false);
      setIsBackendReachable(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    const interval = setInterval(checkConnection, 15000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, [checkConnection, loadWorkspaceState]);

  // Unlock or Enroll Handler
  const handleUnlockOrEnroll = async (e) => {
    e.preventDefault();
    setUnlockError('');

    if (!passphrase || passphrase.length < 6) {
      setUnlockError('Passphrase must be at least 6 characters long.');
      return;
    }

    try {
      if (!isEnrolled) {
        // First-time enrollment on this browser
        if (passphrase !== confirmPassphrase) {
          setUnlockError('Passphrases do not match.');
          return;
        }

        const salt = generateSalt();
        const key = await deriveKey(passphrase, salt);
        const verifier = await computeVerifier(key);

        await OfflineDB.saveAuthMetadata({
          userId,
          salt,
          verifierHash: verifier,
          createdAt: new Date().toISOString(),
        });

        setSessionKey(key);
        setIsUnlocked(true);
        setIsEnrolled(true);
        setIsUnlockModalOpen(false);
        setPassphrase('');
        setConfirmPassphrase('');
        toast({
          title: 'Offline Workspace Enrolled',
          description: 'Your browser is securely configured with AES-256 client-side encryption.',
        });
        await loadWorkspaceState();
      } else {
        // Unlock existing workspace
        const authMeta = await OfflineDB.getAuthMetadata(userId);
        if (!authMeta) {
          setUnlockError('Enrollment data not found for this user account.');
          return;
        }

        const key = await deriveKey(passphrase, authMeta.salt);
        const verifier = await computeVerifier(key);

        if (verifier !== authMeta.verifierHash) {
          setUnlockError('Incorrect passphrase. Please try again.');
          return;
        }

        setSessionKey(key);
        setIsUnlocked(true);
        setIsUnlockModalOpen(false);
        setPassphrase('');
        toast({
          title: 'Workspace Unlocked',
          description: 'Secure session active. Drafts decrypted for this browser session.',
        });
        await loadWorkspaceState();
      }
    } catch (err) {
      console.error('Unlock error:', err);
      setUnlockError('Cryptographic initialization failed: ' + err.message);
    }
  };

  const handleLockWorkspace = () => {
    clearSessionKey();
    setIsUnlocked(false);
    setDrafts([]);
    toast({
      title: 'Workspace Locked',
      description: 'In-memory encryption keys cleared. Drafts remain safely encrypted.',
    });
  };

  // Synchronize Now Handler
  const handleSyncNow = async () => {
    if (!isUnlocked) {
      setIsUnlockModalOpen(true);
      return;
    }

    setIsSyncing(true);
    try {
      const key = getSessionKey();
      const res = await OfflineSyncEngine.pushPendingDrafts(userId, key);
      setLastSyncTime(new Date());
      await loadWorkspaceState();

      if (res.totalProcessed === 0) {
        toast({
          title: 'Up to Date',
          description: 'All offline drafts are already synchronized.',
        });
      } else {
        toast({
          title: 'Synchronization Complete',
          description: res.message,
          variant: res.failedCount > 0 ? 'destructive' : 'default',
        });
      }
    } catch (err) {
      console.error('Sync failed:', err);
      toast({
        title: 'Sync Failed',
        description: err.message,
        variant: 'destructive',
      });
    } finally {
      setIsSyncing(false);
    }
  };

  // Draft Creation: Client Registration
  const handleSaveClientDraft = async (e) => {
    e.preventDefault();
    if (!isUnlocked) {
      setIsUnlockModalOpen(true);
      return;
    }

    if (!clientForm.firstName.trim() || !clientForm.lastName.trim()) {
      toast({
        title: 'Validation Error',
        description: 'First Name and Last Name are required.',
        variant: 'destructive',
      });
      return;
    }

    try {
      const key = getSessionKey();
      const tempId = crypto.randomUUID();
      const payload = {
        temp_id: tempId,
        first_name: clientForm.firstName.trim(),
        last_name: clientForm.lastName.trim(),
        date_of_birth: clientForm.dateOfBirth || null,
        gender: clientForm.gender,
        phone: clientForm.phone.trim(),
        email: clientForm.email.trim(),
        address: clientForm.address.trim(),
        city: clientForm.city,
        province: clientForm.province,
        treaty_number: clientForm.treatyNumber.trim(),
        band_nation: clientForm.bandNation,
        indigenous_identity: clientForm.indigenousIdentity,
        status: clientForm.status,
        risk_level: clientForm.riskLevel,
        notes: clientForm.notes.trim(),
      };

      const envelope = await encryptData(payload, key);
      await OfflineDB.saveDraft({
        id: tempId,
        userId,
        entityType: 'CLIENT',
        title: `${clientForm.firstName.trim()} ${clientForm.lastName.trim()}`,
        subtitle: `Community: ${clientForm.bandNation} • Status: ${clientForm.status}`,
        iv: envelope.iv,
        ciphertext: envelope.ciphertext,
        syncStatus: 'WAITING_TO_SYNC',
      });

      toast({
        title: 'Client Draft Saved',
        description: 'Encrypted and stored in offline storage. Ready to synchronize.',
      });

      setActiveModal(null);
      setClientForm({
        firstName: '',
        lastName: '',
        dateOfBirth: '',
        gender: 'Prefer not to say',
        phone: '',
        email: '',
        address: '',
        city: 'Kamsack',
        province: 'Saskatchewan',
        treatyNumber: '',
        bandNation: 'Cote First Nation',
        indigenousIdentity: 'Status First Nation',
        status: 'Pending Intake',
        riskLevel: 'Low',
        notes: '',
      });
      await loadWorkspaceState();
    } catch (err) {
      toast({
        title: 'Error Saving Draft',
        description: err.message,
        variant: 'destructive',
      });
    }
  };

  // Draft Creation: Intake
  const handleSaveIntakeDraft = async (e) => {
    e.preventDefault();
    if (!isUnlocked) {
      setIsUnlockModalOpen(true);
      return;
    }

    if (!intakeForm.summary.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Summary / Presenting Concerns is required.',
        variant: 'destructive',
      });
      return;
    }

    try {
      const key = getSessionKey();
      const tempId = crypto.randomUUID();
      const payload = {
        summary: intakeForm.summary.trim(),
        received_date: intakeForm.receivedDate,
        received_time: intakeForm.receivedTime,
        received_method: intakeForm.receivedMethod,
        community: intakeForm.community,
        priority: intakeForm.priority,
        risk_level: intakeForm.riskLevel,
        immediate_safety_concerns: intakeForm.immediateSafetyConcerns,
        law_enforcement_involved: intakeForm.lawEnforcementInvolved,
        notes: intakeForm.notes.trim(),
      };

      const envelope = await encryptData(payload, key);
      await OfflineDB.saveDraft({
        id: tempId,
        userId,
        entityType: 'INTAKE',
        title: `Intake Draft: ${intakeForm.community}`,
        subtitle: `Priority: ${intakeForm.priority} • Received: ${intakeForm.receivedDate}`,
        iv: envelope.iv,
        ciphertext: envelope.ciphertext,
        syncStatus: 'WAITING_TO_SYNC',
      });

      toast({
        title: 'Intake Draft Saved',
        description: 'Encrypted and stored in offline storage. Ready to synchronize.',
      });

      setActiveModal(null);
      setIntakeForm({
        summary: '',
        receivedDate: new Date().toISOString().split('T')[0],
        receivedTime: '10:00',
        receivedMethod: 'In Person',
        community: 'Cote First Nation',
        priority: 'Medium',
        riskLevel: 'Low',
        immediateSafetyConcerns: false,
        lawEnforcementInvolved: false,
        notes: '',
      });
      await loadWorkspaceState();
    } catch (err) {
      toast({
        title: 'Error Saving Draft',
        description: err.message,
        variant: 'destructive',
      });
    }
  };

  // Draft Creation: Case Note
  const handleSaveNoteDraft = async (e) => {
    e.preventDefault();
    if (!isUnlocked) {
      setIsUnlockModalOpen(true);
      return;
    }

    if (!noteForm.caseNumber.trim() || !noteForm.title.trim() || !noteForm.summary.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Case Reference, Title, and Clinical Narrative are required.',
        variant: 'destructive',
      });
      return;
    }

    try {
      const key = getSessionKey();
      const tempId = crypto.randomUUID();
      const payload = {
        case_id: noteForm.caseNumber.trim(),
        title: noteForm.title.trim(),
        summary: noteForm.summary.trim(),
        note_type: noteForm.noteType,
        contact_type: noteForm.contactType,
        duration_minutes: parseInt(noteForm.durationMinutes, 10) || 30,
      };

      const envelope = await encryptData(payload, key);
      await OfflineDB.saveDraft({
        id: tempId,
        userId,
        entityType: 'CASE_NOTE',
        title: noteForm.title.trim(),
        subtitle: `Case: ${noteForm.caseNumber.trim()} • Type: ${noteForm.noteType}`,
        iv: envelope.iv,
        ciphertext: envelope.ciphertext,
        syncStatus: 'WAITING_TO_SYNC',
      });

      toast({
        title: 'Case Note Draft Saved',
        description: 'Encrypted and stored locally. Will be submitted as DRAFT upon synchronization.',
      });

      setActiveModal(null);
      setNoteForm({
        caseNumber: '',
        title: '',
        noteType: 'Progress Note',
        summary: '',
        contactType: 'In Person',
        durationMinutes: '30',
      });
      await loadWorkspaceState();
    } catch (err) {
      toast({
        title: 'Error Saving Draft',
        description: err.message,
        variant: 'destructive',
      });
    }
  };

  // View Draft Decryption
  const handleViewDraft = async (draft) => {
    if (!isUnlocked) {
      setIsUnlockModalOpen(true);
      return;
    }

    try {
      const key = getSessionKey();
      const decrypted = await decryptData({ iv: draft.iv, ciphertext: draft.ciphertext }, key);
      setSelectedDraft(draft);
      setDecryptedViewData(decrypted);
      setActiveModal('VIEW');
    } catch (err) {
      toast({
        title: 'Decryption Error',
        description: 'Unable to decrypt record with active key: ' + err.message,
        variant: 'destructive',
      });
    }
  };

  // Delete Draft
  const handleDeleteDraft = async (id) => {
    if (window.confirm('Are you sure you want to delete this offline draft? This cannot be undone.')) {
      await OfflineDB.deleteDraft(id);
      toast({ title: 'Draft Deleted' });
      await loadWorkspaceState();
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Connectivity Status */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded-xl border border-border bg-card/60 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg ${isOnline ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' : 'bg-amber-500/10 text-amber-600 dark:text-amber-400'}`}>
            {isOnline ? <Wifi className="w-5 h-5" /> : <WifiOff className="w-5 h-5" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-foreground">Secure Offline Workspace</h1>
              <Badge variant={isOnline ? 'outline' : 'secondary'} className={isOnline ? 'border-emerald-500/30 text-emerald-600 dark:text-emerald-400' : 'bg-amber-500/20 text-amber-700 dark:text-amber-300'}>
                {isOnline ? (isBackendReachable ? 'Online & Connected' : 'Network Active (Backend Offline)') : 'Offline Field Mode'}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Caseworker: <span className="font-medium text-foreground">{userName}</span> • AES-256 Client-Side Encrypted Storage
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isUnlocked ? (
            <>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleLockWorkspace}
                className="gap-1.5 text-xs text-muted-foreground hover:text-foreground"
              >
                <Lock className="w-3.5 h-3.5" />
                Lock Workspace
              </Button>
              <Button 
                variant="default" 
                size="sm" 
                onClick={handleSyncNow} 
                disabled={isSyncing}
                className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
                {isSyncing ? 'Synchronizing...' : 'Sync Now'}
              </Button>
            </>
          ) : (
            <Button 
              variant="default" 
              size="sm" 
              onClick={() => setIsUnlockModalOpen(true)}
              className="gap-2 bg-accent hover:bg-accent/90 text-accent-foreground shadow-sm"
            >
              <KeyRound className="w-3.5 h-3.5" />
              {isEnrolled ? 'Unlock Workspace' : 'Set Up Offline Access'}
            </Button>
          )}
        </div>
      </div>

      {/* Security & Locking Warning if locked */}
      {!isUnlocked && (
        <Card className="border-amber-500/30 bg-amber-500/5 dark:bg-amber-950/20">
          <CardContent className="pt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
              <div>
                <h3 className="text-sm font-semibold text-foreground">Workspace Is Locked</h3>
                <p className="text-xs text-muted-foreground mt-1">
                  Sensitive child and family drafts are encrypted with AES-GCM 256-bit. Enter your personal passphrase to create, view, or synchronize drafts.
                </p>
              </div>
            </div>
            <Button size="sm" onClick={() => setIsUnlockModalOpen(true)} className="shrink-0 gap-1.5">
              <Unlock className="w-4 h-4" />
              Unlock Now
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card className="bg-card/50">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground">Waiting to Sync</p>
              <p className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1">{metrics.WAITING_TO_SYNC}</p>
            </div>
            <Clock className="w-6 h-6 text-amber-500/40" />
          </CardContent>
        </Card>

        <Card className="bg-card/50">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground">Synchronized</p>
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{metrics.SYNCED}</p>
            </div>
            <CheckCircle2 className="w-6 h-6 text-emerald-500/40" />
          </CardContent>
        </Card>

        <Card className="bg-card/50">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground">Needs Review</p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{metrics.NEEDS_REVIEW}</p>
            </div>
            <AlertTriangle className="w-6 h-6 text-blue-500/40" />
          </CardContent>
        </Card>

        <Card className="bg-card/50">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted-foreground">Failed Records</p>
              <p className="text-2xl font-bold text-rose-600 dark:text-rose-400 mt-1">{metrics.FAILED}</p>
            </div>
            <XCircle className="w-6 h-6 text-rose-500/40" />
          </CardContent>
        </Card>
      </div>

      {/* Action Buttons for Drafting */}
      <div className="flex flex-wrap items-center gap-2.5">
        <Button 
          onClick={() => isUnlocked ? setActiveModal('CLIENT') : setIsUnlockModalOpen(true)}
          className="gap-2 bg-card hover:bg-muted text-foreground border border-border shadow-xs"
        >
          <UserPlus className="w-4 h-4 text-primary" />
          New Client Draft
        </Button>

        <Button 
          onClick={() => isUnlocked ? setActiveModal('INTAKE') : setIsUnlockModalOpen(true)}
          className="gap-2 bg-card hover:bg-muted text-foreground border border-border shadow-xs"
        >
          <FileInput className="w-4 h-4 text-accent" />
          New Intake Draft
        </Button>

        <Button 
          onClick={() => isUnlocked ? setActiveModal('CASE_NOTE') : setIsUnlockModalOpen(true)}
          className="gap-2 bg-card hover:bg-muted text-foreground border border-border shadow-xs"
        >
          <FileText className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          New Case Note Draft
        </Button>
      </div>

      {/* Drafts Repository Table */}
      <Card className="border-border">
        <CardHeader className="p-4 sm:p-6 pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <CardTitle className="text-base font-semibold">Offline Field Drafts Repository</CardTitle>
              <CardDescription className="text-xs">
                Encrypted in browser storage • Safe to close or refresh the window
              </CardDescription>
            </div>

            <Tabs value={activeFilter} onValueChange={setActiveFilter} className="w-auto">
              <TabsList className="h-8">
                <TabsTrigger value="ALL" className="text-xs px-2.5 h-7">All ({metrics.TOTAL})</TabsTrigger>
                <TabsTrigger value="WAITING_TO_SYNC" className="text-xs px-2.5 h-7">Pending ({metrics.WAITING_TO_SYNC})</TabsTrigger>
                <TabsTrigger value="SYNCED" className="text-xs px-2.5 h-7">Synced ({metrics.SYNCED})</TabsTrigger>
                <TabsTrigger value="NEEDS_REVIEW" className="text-xs px-2.5 h-7">Review ({metrics.NEEDS_REVIEW})</TabsTrigger>
                <TabsTrigger value="FAILED" className="text-xs px-2.5 h-7">Failed ({metrics.FAILED})</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {!isUnlocked ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              <Lock className="w-8 h-8 mx-auto mb-2 text-muted-foreground/60" />
              <p>Unlock workspace to view and manage offline records.</p>
            </div>
          ) : drafts.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              <Database className="w-8 h-8 mx-auto mb-2 text-muted-foreground/40" />
              <p>No offline drafts found in this category.</p>
              <p className="text-xs mt-1">Use the buttons above to record client, intake, or note drafts offline.</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {drafts.map((draft) => (
                <div key={draft.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-muted/30 transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm text-foreground">{draft.title}</span>
                      <Badge variant="outline" className="text-[10px] px-1.5 py-0 font-normal">
                        {draft.entityType}
                      </Badge>
                      <Badge 
                        variant="secondary"
                        className={`text-[10px] px-1.5 py-0 ${
                          draft.syncStatus === 'SYNCED' ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300' :
                          draft.syncStatus === 'WAITING_TO_SYNC' ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300' :
                          draft.syncStatus === 'NEEDS_REVIEW' ? 'bg-blue-500/15 text-blue-700 dark:text-blue-300' :
                          'bg-rose-500/15 text-rose-700 dark:text-rose-300'
                        }`}
                      >
                        {draft.syncStatus === 'WAITING_TO_SYNC' ? 'Waiting to Sync' :
                         draft.syncStatus === 'SYNCED' ? 'Authoritative Synced' :
                         draft.syncStatus === 'NEEDS_REVIEW' ? 'Supervisor Review Required' :
                         'Sync Failed'}
                      </Badge>
                    </div>

                    <p className="text-xs text-muted-foreground">{draft.subtitle}</p>

                    {draft.personIdNumber && (
                      <p className="text-xs font-mono text-emerald-600 dark:text-emerald-400">
                        Permanent Person ID: {draft.personIdNumber}
                      </p>
                    )}

                    {draft.referralNumber && (
                      <p className="text-xs font-mono text-emerald-600 dark:text-emerald-400">
                        Permanent Referral #: {draft.referralNumber}
                      </p>
                    )}

                    {draft.errorMessage && (
                      <p className="text-xs text-rose-600 dark:text-rose-400 flex items-center gap-1 mt-1">
                        <AlertTriangle className="w-3 h-3 shrink-0" />
                        {draft.errorMessage}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => handleViewDraft(draft)}
                      className="h-8 px-2.5 text-xs gap-1"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      View
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => handleDeleteDraft(draft.id)}
                      className="h-8 px-2.5 text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-500/10"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
        {lastSyncTime && (
          <CardFooter className="p-3 bg-muted/20 border-t border-border text-[11px] text-muted-foreground flex justify-between">
            <span>Last Synced: {lastSyncTime.toLocaleTimeString()}</span>
            <span>CRBCL Secure Sync Gateway</span>
          </CardFooter>
        )}
      </Card>

      {/* --- UNLOCK / ENROLLMENT MODAL --- */}
      <Dialog open={isUnlockModalOpen} onOpenChange={setIsUnlockModalOpen}>
        <DialogContent className="sm:max-w-[420px]">
          <form onSubmit={handleUnlockOrEnroll}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-primary" />
                {isEnrolled ? 'Unlock Offline Workspace' : 'Set Up Offline Passphrase'}
              </DialogTitle>
              <DialogDescription className="text-xs">
                {isEnrolled 
                  ? 'Enter your personal offline passphrase to derive your in-memory AES-GCM encryption key.'
                  : 'Create a personal offline passphrase. This key never leaves your browser and protects client data offline.'}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 py-4">
              <div className="space-y-1.5">
                <Label htmlFor="passphrase" className="text-xs">Passphrase (min. 6 characters)</Label>
                <Input 
                  id="passphrase"
                  type="password"
                  value={passphrase}
                  onChange={(e) => setPassphrase(e.target.value)}
                  placeholder="Enter secure passphrase..."
                  autoFocus
                />
              </div>

              {!isEnrolled && (
                <div className="space-y-1.5">
                  <Label htmlFor="confirmPassphrase" className="text-xs">Confirm Passphrase</Label>
                  <Input 
                    id="confirmPassphrase"
                    type="password"
                    value={confirmPassphrase}
                    onChange={(e) => setConfirmPassphrase(e.target.value)}
                    placeholder="Confirm your passphrase..."
                  />
                </div>
              )}

              {unlockError && (
                <div className="text-xs text-rose-600 flex items-center gap-1.5 pt-1">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                  <span>{unlockError}</span>
                </div>
              )}
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setIsUnlockModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm">
                {isEnrolled ? 'Unlock' : 'Enroll & Unlock'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- NEW CLIENT DRAFT MODAL --- */}
      <Dialog open={activeModal === 'CLIENT'} onOpenChange={(open) => !open && setActiveModal(null)}>
        <DialogContent className="sm:max-w-[560px] max-h-[85vh] overflow-y-auto">
          <form onSubmit={handleSaveClientDraft}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-primary" />
                New Client Registration Draft
              </DialogTitle>
              <DialogDescription className="text-xs">
                Creates an encrypted local draft. Canonical Person & Client records will be generated upon synchronization.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 py-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="cFirstName">First Name *</Label>
                  <Input 
                    id="cFirstName" 
                    required 
                    value={clientForm.firstName} 
                    onChange={(e) => setClientForm({ ...clientForm, firstName: e.target.value })} 
                    placeholder="e.g. Wapusk"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="cLastName">Last Name *</Label>
                  <Input 
                    id="cLastName" 
                    required 
                    value={clientForm.lastName} 
                    onChange={(e) => setClientForm({ ...clientForm, lastName: e.target.value })} 
                    placeholder="e.g. Muskego"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="cDOB">Date of Birth</Label>
                  <Input 
                    id="cDOB" 
                    type="date"
                    value={clientForm.dateOfBirth} 
                    onChange={(e) => setClientForm({ ...clientForm, dateOfBirth: e.target.value })} 
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="cTreaty">Treaty / Status #</Label>
                  <Input 
                    id="cTreaty" 
                    value={clientForm.treatyNumber} 
                    onChange={(e) => setClientForm({ ...clientForm, treatyNumber: e.target.value })} 
                    placeholder="e.g. TR-654321"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="cPhone">Phone Number</Label>
                  <Input 
                    id="cPhone" 
                    value={clientForm.phone} 
                    onChange={(e) => setClientForm({ ...clientForm, phone: e.target.value })} 
                    placeholder="e.g. 306-555-0199"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="cEmail">Email Address</Label>
                  <Input 
                    id="cEmail" 
                    type="email"
                    value={clientForm.email} 
                    onChange={(e) => setClientForm({ ...clientForm, email: e.target.value })} 
                    placeholder="e.g. client@example.com"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <Label htmlFor="cBand">First Nation / Band</Label>
                <Input 
                  id="cBand" 
                  value={clientForm.bandNation} 
                  onChange={(e) => setClientForm({ ...clientForm, bandNation: e.target.value })} 
                  placeholder="e.g. Cote First Nation"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="cNotes">Field Notes / Intake Observations</Label>
                <Textarea 
                  id="cNotes" 
                  rows={3} 
                  value={clientForm.notes} 
                  onChange={(e) => setClientForm({ ...clientForm, notes: e.target.value })} 
                  placeholder="Observations, family background, or notes..."
                />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setActiveModal(null)}>Cancel</Button>
              <Button type="submit" size="sm">Save Encrypted Draft</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- NEW INTAKE DRAFT MODAL --- */}
      <Dialog open={activeModal === 'INTAKE'} onOpenChange={(open) => !open && setActiveModal(null)}>
        <DialogContent className="sm:max-w-[540px] max-h-[85vh] overflow-y-auto">
          <form onSubmit={handleSaveIntakeDraft}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileInput className="w-5 h-5 text-accent" />
                New Intake & Referral Draft
              </DialogTitle>
              <DialogDescription className="text-xs">
                Creates an encrypted intake draft. Authoritative referral number (INT-YYYY-NNNNNN) will be assigned on synchronization.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 py-4 text-xs">
              <div className="space-y-1">
                <Label htmlFor="iSummary">Presenting Concerns & Summary *</Label>
                <Textarea 
                  id="iSummary" 
                  required 
                  rows={3} 
                  value={intakeForm.summary} 
                  onChange={(e) => setIntakeForm({ ...intakeForm, summary: e.target.value })} 
                  placeholder="Summary of referral reasons, child wellness needs, and family context..."
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="iCommunity">Community</Label>
                  <Input 
                    id="iCommunity" 
                    value={intakeForm.community} 
                    onChange={(e) => setIntakeForm({ ...intakeForm, community: e.target.value })} 
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="iDate">Received Date</Label>
                  <Input 
                    id="iDate" 
                    type="date"
                    value={intakeForm.receivedDate} 
                    onChange={(e) => setIntakeForm({ ...intakeForm, receivedDate: e.target.value })} 
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="iPriority">Priority</Label>
                  <select 
                    id="iPriority"
                    className="w-full h-9 rounded-md border border-input bg-transparent px-3 py-1 text-xs shadow-xs"
                    value={intakeForm.priority}
                    onChange={(e) => setIntakeForm({ ...intakeForm, priority: e.target.value })}
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Urgent">Urgent</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="iMethod">Method Received</Label>
                  <Input 
                    id="iMethod" 
                    value={intakeForm.receivedMethod} 
                    onChange={(e) => setIntakeForm({ ...intakeForm, receivedMethod: e.target.value })} 
                  />
                </div>
              </div>

              <div className="flex items-center gap-4 pt-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={intakeForm.immediateSafetyConcerns} 
                    onChange={(e) => setIntakeForm({ ...intakeForm, immediateSafetyConcerns: e.target.checked })} 
                    className="rounded border-input"
                  />
                  <span>Immediate Safety Concerns</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={intakeForm.lawEnforcementInvolved} 
                    onChange={(e) => setIntakeForm({ ...intakeForm, lawEnforcementInvolved: e.target.checked })} 
                    className="rounded border-input"
                  />
                  <span>Law Enforcement Involved</span>
                </label>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setActiveModal(null)}>Cancel</Button>
              <Button type="submit" size="sm">Save Encrypted Draft</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- NEW CASE NOTE DRAFT MODAL --- */}
      <Dialog open={activeModal === 'CASE_NOTE'} onOpenChange={(open) => !open && setActiveModal(null)}>
        <DialogContent className="sm:max-w-[540px] max-h-[85vh] overflow-y-auto">
          <form onSubmit={handleSaveNoteDraft}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                New Case Note Draft
              </DialogTitle>
              <DialogDescription className="text-xs">
                Saved as DRAFT in offline storage. Never automatically signed or finalized upon synchronization.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 py-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="nCase">Case ID or Number *</Label>
                  <Input 
                    id="nCase" 
                    required 
                    value={noteForm.caseNumber} 
                    onChange={(e) => setNoteForm({ ...noteForm, caseNumber: e.target.value })} 
                    placeholder="e.g. CASE-2026-0042"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="nType">Note Type</Label>
                  <select 
                    id="nType"
                    className="w-full h-9 rounded-md border border-input bg-transparent px-3 py-1 text-xs shadow-xs"
                    value={noteForm.noteType}
                    onChange={(e) => setNoteForm({ ...noteForm, noteType: e.target.value })}
                  >
                    <option value="Progress Note">Progress Note</option>
                    <option value="Home Visit">Home Visit</option>
                    <option value="Client Contact">Client Contact</option>
                    <option value="Collateral Contact">Collateral Contact</option>
                    <option value="Case Assessment">Case Assessment</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <Label htmlFor="nTitle">Subject / Title *</Label>
                <Input 
                  id="nTitle" 
                  required 
                  value={noteForm.title} 
                  onChange={(e) => setNoteForm({ ...noteForm, title: e.target.value })} 
                  placeholder="e.g. Family In-Person Wellness Check"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="nSummary">Clinical Observations / Narrative *</Label>
                <Textarea 
                  id="nSummary" 
                  required 
                  rows={4} 
                  value={noteForm.summary} 
                  onChange={(e) => setNoteForm({ ...noteForm, summary: e.target.value })} 
                  placeholder="Detailed notes of observations, participant statements, home environment..."
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="nContact">Contact Method</Label>
                  <Input 
                    id="nContact" 
                    value={noteForm.contactType} 
                    onChange={(e) => setNoteForm({ ...noteForm, contactType: e.target.value })} 
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="nDuration">Duration (minutes)</Label>
                  <Input 
                    id="nDuration" 
                    type="number"
                    value={noteForm.durationMinutes} 
                    onChange={(e) => setNoteForm({ ...noteForm, durationMinutes: e.target.value })} 
                  />
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setActiveModal(null)}>Cancel</Button>
              <Button type="submit" size="sm">Save Encrypted Draft</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* --- VIEW DRAFT DETAILS MODAL --- */}
      <Dialog open={activeModal === 'VIEW'} onOpenChange={(open) => !open && setActiveModal(null)}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-sm">
              <Eye className="w-4 h-4 text-primary" />
              Decrypted Draft: {selectedDraft?.title}
            </DialogTitle>
            <DialogDescription className="text-xs">
              Record ID: <code>{selectedDraft?.id}</code>
            </DialogDescription>
          </DialogHeader>

          <div className="py-3 max-h-[60vh] overflow-y-auto text-xs space-y-2">
            {decryptedViewData && (
              <pre className="p-3 rounded-lg bg-muted/60 font-mono text-[11px] overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(decryptedViewData, null, 2)}
              </pre>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" size="sm" onClick={() => setActiveModal(null)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
