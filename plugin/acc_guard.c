/*
 * acc_guard - drop-in HID.DLL for ASTRO Command Center 1.0.226 (A50 Gen 4 / "Mimas").
 * Put it next to "ASTRO Command Center.exe". It forwards every export to the real
 * Windows hid.dll and changes ACC only in memory - no ACC file is modified.
 *
 *  1. LOG: every HID packet exchanged with the base (VID 9886) is appended to
 *     %LOCALAPPDATA%\Astro Gaming\ASTRO Command Center\Logs\acc_guard_hid.log
 *  2. GUARD: while a firmware component is being written (start 0x42/0x48/0xF2/0xF8 ->
 *     end 0x44/0x4A/0xF4/0xFA) and during pairing (0x5B -> 0xFC), only the updating
 *     thread may talk to the base; writes from other threads fail with ERROR_BUSY
 *     (ACC logs "setReport failed" and carries on).
 *  3. TOLERANCE: ACC ignores HID_ERROR_SLAVE_TIMEOUT on headset data blocks (0xF3/0xF9)
 *     only on some hardware revisions; this makes it unconditional. Applied in memory,
 *     only if the expected bytes of ACC 1.0.226 are found.
 *
 * Build (clang/lld, no C runtime):
 *   llvm-dlltool -m i386 -d kernel32.def -l kernel32.lib -k
 *   clang -target i686-pc-windows-msvc -O2 -ffreestanding -fno-builtin -fno-stack-protector -c acc_guard.c
 *   lld-link /dll /nodefaultlib /entry:DllMain@12 /def:hid.def /out:HID.DLL /machine:x86 /safeseh:no acc_guard.obj kernel32.lib
 *
 * USE AT YOUR OWN RISK. Not affiliated with ASTRO Gaming or Logitech.
 */
typedef int BOOL;
typedef unsigned long DWORD;
typedef unsigned short WORD;
typedef unsigned char BYTE;
typedef void *HANDLE, *HMODULE, *LPVOID;
typedef const void *LPCVOID;
typedef const unsigned short *LPCWSTR;
typedef const char *LPCSTR;
typedef unsigned int UINT;
#define WINAPI __stdcall
#define NULL ((void *)0)
#define INVALID_HANDLE_VALUE ((HANDLE)(long)-1)

typedef struct { DWORD Internal, InternalHigh, Offset, OffsetHigh; HANDLE hEvent; } OVERLAPPED;
typedef struct { WORD wYear, wMonth, wDayOfWeek, wDay, wHour, wMinute, wSecond, wMilliseconds; } SYSTEMTIME;
typedef struct { DWORD a[6]; } CRITICAL_SECTION; /* 24 bytes on x86 */

__declspec(dllimport) HMODULE WINAPI LoadLibraryA(LPCSTR);
__declspec(dllimport) void *WINAPI GetProcAddress(HMODULE, LPCSTR);
__declspec(dllimport) HMODULE WINAPI GetModuleHandleA(LPCSTR);
__declspec(dllimport) UINT WINAPI GetSystemDirectoryA(char *, UINT);
__declspec(dllimport) BOOL WINAPI VirtualProtect(LPVOID, DWORD, DWORD, DWORD *);
__declspec(dllimport) HANDLE WINAPI CreateFileA(LPCSTR, DWORD, DWORD, LPVOID, DWORD, DWORD, HANDLE);
__declspec(dllimport) HANDLE WINAPI CreateFileW(LPCWSTR, DWORD, DWORD, LPVOID, DWORD, DWORD, HANDLE);
__declspec(dllimport) BOOL WINAPI WriteFile(HANDLE, LPCVOID, DWORD, DWORD *, OVERLAPPED *);
__declspec(dllimport) BOOL WINAPI ReadFile(HANDLE, LPVOID, DWORD, DWORD *, OVERLAPPED *);
__declspec(dllimport) BOOL WINAPI GetOverlappedResult(HANDLE, OVERLAPPED *, DWORD *, BOOL);
__declspec(dllimport) BOOL WINAPI CloseHandle(HANDLE);
__declspec(dllimport) DWORD WINAPI GetCurrentThreadId(void);
__declspec(dllimport) DWORD WINAPI GetTickCount(void);
__declspec(dllimport) void WINAPI GetLocalTime(SYSTEMTIME *);
__declspec(dllimport) void WINAPI SetLastError(DWORD);
__declspec(dllimport) DWORD WINAPI GetLastError(void);
__declspec(dllimport) DWORD WINAPI GetEnvironmentVariableA(LPCSTR, char *, DWORD);
__declspec(dllimport) void WINAPI InitializeCriticalSection(CRITICAL_SECTION *);
__declspec(dllimport) void WINAPI EnterCriticalSection(CRITICAL_SECTION *);
__declspec(dllimport) void WINAPI LeaveCriticalSection(CRITICAL_SECTION *);
__declspec(dllimport) DWORD WINAPI SetFilePointer(HANDLE, long, long *, DWORD);

/* ---------- tiny helpers (no CRT) ---------- */
void *memset(void *d, int c, unsigned n) { BYTE *p = d; while (n--) *p++ = (BYTE)c; return d; }
void *memcpy(void *d, const void *s, unsigned n) { BYTE *p = d; const BYTE *q = s; while (n--) *p++ = *q++; return d; }
static int slen(const char *s) { int n = 0; while (s[n]) n++; return n; }
static int seq(const char *a, const char *b) { while (*a && *a == *b) { a++; b++; } return *a == *b; }
static char *scat(char *d, const char *s) { while (*d) d++; while ((*d++ = *s++) != 0) {} return d - 1; }

/* ---------- original functions ---------- */
typedef BOOL (WINAPI *WriteFile_t)(HANDLE, LPCVOID, DWORD, DWORD *, OVERLAPPED *);
typedef BOOL (WINAPI *ReadFile_t)(HANDLE, LPVOID, DWORD, DWORD *, OVERLAPPED *);
typedef BOOL (WINAPI *GetOvl_t)(HANDLE, OVERLAPPED *, DWORD *, BOOL);
typedef HANDLE (WINAPI *CreateFileW_t)(LPCWSTR, DWORD, DWORD, LPVOID, DWORD, DWORD, HANDLE);
static WriteFile_t o_WriteFile;
static ReadFile_t o_ReadFile;
static GetOvl_t o_GetOvl;
static CreateFileW_t o_CreateFileW;

static CRITICAL_SECTION cs;
static HANDLE logf = INVALID_HANDLE_VALUE;

#define MAXH 16
static HANDLE hid_handles[MAXH];
#define MAXR 32
static struct { OVERLAPPED *ov; BYTE *buf; HANDLE h; } reads[MAXR];

static volatile DWORD guard_owner, guard_until;   /* guard state */
static volatile int guard_on, guard_release_on_rx;

/* ---------- log ---------- */
static void log_line(const char *tag, const BYTE *data, DWORD n)
{
    static const char hx[] = "0123456789ABCDEF";
    char line[400];
    SYSTEMTIME t; DWORD i, k = 0, w;
    if (logf == INVALID_HANDLE_VALUE) return;
    GetLocalTime(&t);
    line[k++] = '0' + t.wHour / 10; line[k++] = '0' + t.wHour % 10; line[k++] = ':';
    line[k++] = '0' + t.wMinute / 10; line[k++] = '0' + t.wMinute % 10; line[k++] = ':';
    line[k++] = '0' + t.wSecond / 10; line[k++] = '0' + t.wSecond % 10; line[k++] = '.';
    line[k++] = '0' + t.wMilliseconds / 100; line[k++] = '0' + (t.wMilliseconds / 10) % 10;
    line[k++] = '0' + t.wMilliseconds % 10; line[k++] = ' ';
    { DWORD tid = GetCurrentThreadId(); int s; for (s = 28; s >= 0; s -= 4) line[k++] = hx[(tid >> s) & 15]; }
    line[k++] = ' ';
    while (*tag && k < 60) line[k++] = *tag++;
    line[k++] = ' ';
    if (n > 64) n = 64;
    for (i = 0; i < n && k < sizeof(line) - 4; i++) { line[k++] = hx[data[i] >> 4]; line[k++] = hx[data[i] & 15]; line[k++] = ' '; }
    line[k++] = '\r'; line[k++] = '\n';
    EnterCriticalSection(&cs);
    o_WriteFile(logf, line, k, &w, NULL);
    LeaveCriticalSection(&cs);
}

static void log_text(const char *s) { log_line(s, (const BYTE *)"", 0); }

static int is_hid(HANDLE h)
{
    int i; if (!h) return 0;
    for (i = 0; i < MAXH; i++) if (hid_handles[i] == h) return 1;
    return 0;
}

static int in_set(BYTE c, const BYTE *set, int n) { int i; for (i = 0; i < n; i++) if (set[i] == c) return 1; return 0; }
static const BYTE START_CMDS[] = { 0x42, 0x48, 0xF2, 0xF8, 0x5B };
static const BYTE END_CMDS[]   = { 0x44, 0x4A, 0xF4, 0xFA, 0xFC };

static void rx_done(void)
{
    if (guard_on && guard_release_on_rx) { guard_on = 0; guard_release_on_rx = 0; log_text("GUARD off"); }
}

/* ---------- hook ---------- */
static HANDLE WINAPI h_CreateFileW(LPCWSTR name, DWORD a, DWORD s, LPVOID sa, DWORD c, DWORD f, HANDLE t)
{
    HANDLE h = o_CreateFileW(name, a, s, sa, c, f, t);
    if (h != INVALID_HANDLE_VALUE && name) {
        const unsigned short *p = name; int found = 0;
        for (; *p; p++) {
            if ((p[0] | 32) == 'v' && (p[1] | 32) == 'i' && (p[2] | 32) == 'd' && p[3] == '_' &&
                p[4] == '9' && p[5] == '8' && p[6] == '8' && p[7] == '6') { found = 1; break; }
        }
        if (found) {
            int i; EnterCriticalSection(&cs);
            for (i = 0; i < MAXH; i++) if (!hid_handles[i] || hid_handles[i] == h) { hid_handles[i] = h; break; }
            LeaveCriticalSection(&cs);
            log_text("OPENED device 9886");
        }
    }
    return h;
}

static BOOL WINAPI h_WriteFile(HANDLE h, LPCVOID buf, DWORD n, DWORD *wr, OVERLAPPED *ov)
{
    if (is_hid(h) && buf && n >= 2) {
        const BYTE *b = buf; BYTE cmd = b[1];
        DWORD me = GetCurrentThreadId(), now = GetTickCount();
        if (guard_on && (long)(guard_until - now) <= 0) { guard_on = 0; log_text("GUARD off (timeout)"); }
        if (guard_on && guard_owner != me) {
            log_line("BLOCKED", b, n);
            SetLastError(170 /* ERROR_BUSY */);
            return 0;
        }
        if (in_set(cmd, START_CMDS, sizeof START_CMDS) && (!guard_on || guard_owner == me)) {
            guard_owner = me; guard_until = now + 180000; guard_on = 1; guard_release_on_rx = 0;
            log_text("GUARD on");
        } else if (guard_on && guard_owner == me && in_set(cmd, END_CMDS, sizeof END_CMDS)) {
            guard_until = now + 5000;   /* released on the next response (5 s max) */
            guard_release_on_rx = 1;
        }
        log_line("TX", b, n);
    }
    return o_WriteFile(h, buf, n, wr, ov);
}

static BOOL WINAPI h_ReadFile(HANDLE h, LPVOID buf, DWORD n, DWORD *rd, OVERLAPPED *ov)
{
    BOOL r = o_ReadFile(h, buf, n, rd, ov);
    if (is_hid(h)) {
        if (r && rd && *rd) { log_line("RX", buf, *rd); rx_done(); }
        else if (ov) {
            int i; EnterCriticalSection(&cs);
            for (i = 0; i < MAXR; i++) if (!reads[i].ov || reads[i].ov == ov) {
                reads[i].ov = ov; reads[i].buf = buf; reads[i].h = h; break; }
            LeaveCriticalSection(&cs);
        }
    }
    return r;
}

static BOOL WINAPI h_GetOvl(HANDLE h, OVERLAPPED *ov, DWORD *n, BOOL wait)
{
    BOOL r = o_GetOvl(h, ov, n, wait);
    if (r && ov && is_hid(h)) {
        int i; BYTE *buf = NULL;
        EnterCriticalSection(&cs);
        for (i = 0; i < MAXR; i++) if (reads[i].ov == ov && reads[i].h == h) { buf = reads[i].buf; reads[i].ov = NULL; break; }
        LeaveCriticalSection(&cs);
        if (buf && n && *n) { log_line("RX", buf, *n); rx_done(); }
    }
    return r;
}

/* ---------- IAT hook of the main executable ---------- */
static void hook_iat(BYTE *base)
{
    DWORD pe = *(DWORD *)(base + 0x3C);
    DWORD imp = *(DWORD *)(base + pe + 0x18 + 0x60 + 8);   /* data directory[1] */
    DWORD *desc = (DWORD *)(base + imp);
    for (; desc[3]; desc += 5) {
        const char *dll = (const char *)(base + desc[3]);
        DWORD *orig = (DWORD *)(base + (desc[0] ? desc[0] : desc[4]));
        DWORD *iat = (DWORD *)(base + desc[4]);
        if ((dll[0] | 32) != 'k' || (dll[1] | 32) != 'e' || (dll[2] | 32) != 'r') continue;
        for (; *orig; orig++, iat++) {
            const char *fn; void *repl = NULL;
            if (*orig & 0x80000000) continue;
            fn = (const char *)(base + *orig + 2);
            if (!slen(fn)) continue;
            if (seq(fn, "WriteFile")) { o_WriteFile = (WriteFile_t)*iat; repl = h_WriteFile; }
            else if (seq(fn, "ReadFile")) { o_ReadFile = (ReadFile_t)*iat; repl = h_ReadFile; }
            else if (seq(fn, "GetOverlappedResult")) { o_GetOvl = (GetOvl_t)*iat; repl = h_GetOvl; }
            else if (seq(fn, "CreateFileW")) { o_CreateFileW = (CreateFileW_t)*iat; repl = h_CreateFileW; }
            if (repl) {
                DWORD old;
                VirtualProtect(iat, 4, 0x04, &old);
                *iat = (DWORD)repl;
                VirtualProtect(iat, 4, old, &old);
            }
        }
    }
}

/* ---------- SLAVE_TIMEOUT tolerance patch ---------- */
static void patch_tolerance(BYTE *base)
{
    BYTE *p = base + 0x94CFE;                 /* cmp dword [ebp-0x5c],5 ; jne +0x13 */
    static const BYTE expect[6] = { 0x83, 0x7D, 0xA4, 0x05, 0x75, 0x13 };
    int i; DWORD old;
    for (i = 0; i < 6; i++) if (p[i] != expect[i]) { log_text("PATCH: unexpected bytes, NOT applied (different ACC version?)"); return; }
    VirtualProtect(p + 4, 2, 0x40, &old);
    p[4] = 0x90; p[5] = 0x90;
    VirtualProtect(p + 4, 2, old, &old);
    log_text("PATCH applied");
}

/* ---------- forward all hid.dll exports ---------- */
static HMODULE real_hid;
#define HID_FUNCS(X) \
 X(HidD_FlushQueue) X(HidD_FreePreparsedData) X(HidD_GetAttributes) X(HidD_GetConfiguration) \
 X(HidD_GetFeature) X(HidD_GetHidGuid) X(HidD_GetIndexedString) X(HidD_GetInputReport) \
 X(HidD_GetManufacturerString) X(HidD_GetMsGenreDescriptor) X(HidD_GetNumInputBuffers) \
 X(HidD_GetPhysicalDescriptor) X(HidD_GetPreparsedData) X(HidD_GetProductString) \
 X(HidD_GetSerialNumberString) X(HidD_Hello) X(HidD_SetConfiguration) X(HidD_SetFeature) \
 X(HidD_SetNumInputBuffers) X(HidD_SetOutputReport) X(HidP_GetButtonArray) X(HidP_GetButtonCaps) \
 X(HidP_GetCaps) X(HidP_GetData) X(HidP_GetExtendedAttributes) X(HidP_GetLinkCollectionNodes) \
 X(HidP_GetScaledUsageValue) X(HidP_GetSpecificButtonCaps) X(HidP_GetSpecificValueCaps) \
 X(HidP_GetUsageValue) X(HidP_GetUsageValueArray) X(HidP_GetUsages) X(HidP_GetUsagesEx) \
 X(HidP_GetValueCaps) X(HidP_GetVersionInternal) X(HidP_InitializeReportForID) \
 X(HidP_MaxDataListLength) X(HidP_MaxUsageListLength) X(HidP_SetButtonArray) X(HidP_SetData) \
 X(HidP_SetScaledUsageValue) X(HidP_SetUsageValue) X(HidP_SetUsageValueArray) X(HidP_SetUsages) \
 X(HidP_TranslateUsagesToI8042ScanCodes) X(HidP_UnsetUsages) X(HidP_UsageListDifference)

#define DECL_PTR(n) void *p_##n;
HID_FUNCS(DECL_PTR)
#define STUB(n) __attribute__((naked)) void n(void) { __asm__ volatile ("jmp *_p_" #n); }
HID_FUNCS(STUB)
#define RESOLVE(n) p_##n = GetProcAddress(real_hid, #n);

BOOL WINAPI DllMain(HMODULE self, DWORD reason, LPVOID reserved)
{
    if (reason == 1) {
        char path[300]; BYTE *exe;
        path[0] = 0;
        GetSystemDirectoryA(path, 260);
        scat(path, "\\hid.dll");
        real_hid = LoadLibraryA(path);
        if (!real_hid) return 0;
        HID_FUNCS(RESOLVE)
        InitializeCriticalSection(&cs);

        path[0] = 0;
        if (GetEnvironmentVariableA("LOCALAPPDATA", path, 200)) {
            scat(path, "\\Astro Gaming\\ASTRO Command Center\\Logs\\acc_guard_hid.log");
            logf = CreateFileA(path, 0x40000000 /*GENERIC_WRITE*/, 1 | 2, NULL, 4 /*OPEN_ALWAYS*/, 0x80, NULL);
            if (logf != INVALID_HANDLE_VALUE) SetFilePointer(logf, 0, NULL, 2 /*FILE_END*/);
        }
        exe = (BYTE *)GetModuleHandleA(NULL);
        hook_iat(exe);
        if (!o_WriteFile) o_WriteFile = WriteFile;   /* fallback */
        log_text("=== acc_guard loaded ===");
        patch_tolerance(exe);
    }
    return 1;
}
