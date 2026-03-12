import { useState } from 'react';

export const useProviderSettingsState = () => {
    const [providerType, setProviderType] = useState('openai');
    const [providerId, setProviderId] = useState('openai-main');
    const [modelId, setModelId] = useState('');
    const [providerSearch, setProviderSearch] = useState('');
    const [modelSearch, setModelSearch] = useState('');
    const [providerDropdownOpen, setProviderDropdownOpen] = useState(false);
    const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
    const [authMode, setAuthMode] = useState('api_key');
    const [apiKey, setApiKey] = useState('');
    const [account, setAccount] = useState('');
    const [baseUrl, setBaseUrl] = useState('');
    const [org, setOrg] = useState('');
    const [validateResult, setValidateResult] = useState<any>(null);
    const [installState, setInstallState] = useState<{
        status: string;
        message: string;
        progress?: number;
        job_id?: string;
        is_cli?: boolean;
        dependency_id?: string;
    } | null>(null);
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [deviceLoginState, setDeviceLoginState] = useState<{
        status: string;
        verification_url?: string;
        user_code?: string;
        message?: string;
        action?: string;
    } | null>(null);
    const [cliAuthStatus, setCliAuthStatus] = useState<{
        authenticated: boolean;
        method?: string | null;
        email?: string | null;
        plan?: string | null;
        detail?: string;
    } | null>(null);
    const [cliAuthLoading, setCliAuthLoading] = useState(false);
    const [recommendation, setRecommendation] = useState<any>(null);
    const [loadingRecommendation, setLoadingRecommendation] = useState(true);

    return {
        providerType, setProviderType,
        providerId, setProviderId,
        modelId, setModelId,
        providerSearch, setProviderSearch,
        modelSearch, setModelSearch,
        providerDropdownOpen, setProviderDropdownOpen,
        modelDropdownOpen, setModelDropdownOpen,
        authMode, setAuthMode,
        apiKey, setApiKey,
        account, setAccount,
        baseUrl, setBaseUrl,
        org, setOrg,
        validateResult, setValidateResult,
        installState, setInstallState,
        showAdvanced, setShowAdvanced,
        deviceLoginState, setDeviceLoginState,
        cliAuthStatus, setCliAuthStatus,
        cliAuthLoading, setCliAuthLoading,
        recommendation, setRecommendation,
        loadingRecommendation, setLoadingRecommendation,
    };
};
