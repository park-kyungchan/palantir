#include <windows.h>

// 한글 2010 SE+ 이상의 자동화 보안 승인 모듈
// exports 함수: GetFilePathCheckClass

#define EXPORT __declspec(dllexport)

extern "C" {
    // 필수 내보내기 함수
    EXPORT BOOL WINAPI GetFilePathCheckClass(
        const char *filePath, 
        const char *userValue, 
        char *outBuffer, 
        int bufferSize
    ) {
        // 무조건 통과 (팝업 억제)
        // outBuffer에 "CDllImage" 등의 클래스명이나 특정 값을 넣을 필요 없이
        // 단순히 TRUE를 리턴하는 것만으로도 승인되는 경우가 많음.
        // 하지만 확실히 하기 위해 안전한 문자열 복사.
        if (outBuffer && bufferSize > 0) {
            outBuffer[0] = '\0'; 
        }
        return TRUE; // 승인
    }
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
    case DLL_PROCESS_ATTACH:
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}
