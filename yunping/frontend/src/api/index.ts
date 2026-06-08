import client from './client';

// ============ 认证接口 ============

export interface LoginRequest { username: string; password: string; }
export interface RegisterRequest { username: string; password: string; role?: string; assigned_bases?: string[]; }
export interface UserInfo { id: string; username: string; role: string; assigned_bases: string; is_active: boolean; }
export interface TokenData { access_token: string; token_type: string; user: UserInfo; }

export const login = (data: LoginRequest) => client.post<TokenData>('/v1/auth/login', data);
export const register = (data: RegisterRequest) => client.post<UserInfo>('/v1/auth/register', data);
export const getMe = () => client.get<UserInfo>('/v1/auth/me');

// ============ 标准条目接口 ============

export interface Item { id: string; requirement: string; section: string; item_type: string | null; status: string; created_at: string; updated_at: string; }

export const getItems = (params?: { section?: string; status?: string }) => client.get('/v1/items', { params });
export const getItem = (itemId: string) => client.get<Item>(`/v1/items/${itemId}`);
export const createItem = (data: { id: string; requirement: string; section: string; item_type?: string }) => client.post<Item>('/v1/items', data);
export const updateItem = (itemId: string, data: any) => client.put<Item>(`/v1/items/${itemId}`, data);
export const deleteItem = (itemId: string) => client.delete(`/v1/items/${itemId}`);

// ============ 基地接口 ============

export interface BaseInfo { id: string; name: string; code: string; declaration_status: string; created_at: string; admin_user_names?: string[]; }

export const getBases = () => client.get('/v1/bases');
export const createBase = (data: { name: string; code: string }) => client.post<BaseInfo>('/v1/bases', data);
export const updateBase = (baseId: string, data: { name?: string; code?: string; declaration_status?: string }) => client.put<BaseInfo>(`/v1/bases/${baseId}`, data);
export const deleteBase = (baseId: string) => client.delete(`/v1/bases/${baseId}`);

// ============ 用户管理接口 ============

export interface UserDetail { id: string; username: string; role: string; assigned_bases: string; is_active: boolean; created_at: string; base_details?: { id: string; name: string; code: string }[]; }

export const getUsers = () => client.get('/v1/users');
export const createUser = (data: { username: string; password: string; role?: string; assigned_bases: string[] }) => client.post<UserDetail>('/v1/users', data);
export const updateUser = (userId: string, data: { role?: string; assigned_bases?: string[]; is_active?: boolean }) => client.put<UserDetail>(`/v1/users/${userId}`, data);
export const deleteUser = (userId: string) => client.delete(`/v1/users/${userId}`);

// ============ 材料接口 ============

export interface Material { id: string; item_id: string; base_id: string; material_type: string; file_format: string | null; file_path: string | null; content_text: string | null; version: number; uploaded_at: string; }

export const uploadMaterial = (formData: FormData) => client.post<Material>('/v1/materials/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
export const fillMaterial = (data: { item_id: string; base_id: string; material_type: string; content_text?: string }) => client.post<Material>('/v1/materials/fill', data);
export const getMaterials = (itemId: string, baseId: string) => client.get(`/v1/materials/${itemId}/${baseId}`);

// ============ 智能审核接口 ============

export interface AuditResult { audit_result: string; score: number; diagnosis: string; suggestion: string; differences: any[]; standard_interpretation: string; }
export interface AuditRecord { id: string; item_id: string; base_id: string; result: string; score: number | null; diagnosis: string | null; suggestion: string | null; auditor: string; audited_at: string; }

export const runAudit = (data: { item_id: string; base_id: string }) => client.post<AuditResult>('/v1/audit/run', data);
export const getAuditResult = (itemId: string, baseId: string) => client.get<AuditRecord>(`/v1/audit/result/${itemId}/${baseId}`);
export const getBaseAuditResults = (baseId: string) => client.get(`/v1/audit/results/${baseId}`);

// ============ 标杆管理接口 ============

export interface Benchmark { id: string; name: string; description: string | null; status: string; created_at: string; }

export const getBenchmarks = () => client.get('/v1/benchmarks');
export const createBenchmark = (data: { name: string; description?: string }) => client.post<Benchmark>('/v1/benchmarks', data);
export const uploadBenchmarkMaterial = (formData: FormData) => client.post('/v1/benchmarks/materials/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });

// ============ 交互引导接口 ============

export const runGuide = (data: { item_id: string; base_id: string; user_input?: string }) => client.post('/v1/guide', data);

// ============ LLM配置接口 ============

export const createLLMConfig = (data: { base_url: string; model_id: string; api_key: string; is_default?: boolean }) => client.post('/v1/llm-configs', data);
export const getLLMConfigs = () => client.get('/v1/llm-configs');

// ============ 申报书刷新模板接口 ============

export interface DeclarationTemplate {
  template: { id: number; name: string; document_type: string; file_path: string; status: string; created_at: string; updated_at: string };
  category: string;
  parsed_content: { content_type: string; content_data: string }[];
  template_info: { paragraphs_count?: number; tables_count?: number; sections_count?: number; error?: string };
}

export const uploadDeclarationTemplate = (category: string, formData: FormData) =>
  client.post<DeclarationTemplate>(`/v1/declaration-templates/${category}/upload`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
export const getCategoryTemplates = (category: string) => client.get(`/v1/declaration-templates/${category}`);
export const getAllCategoryOverview = () => client.get('/v1/declaration-templates');
export const deleteDeclarationTemplate = (templateId: number) => client.delete(`/v1/declaration-templates/${templateId}`);

// 申报书刷新 - 基地用户编辑保存
export interface ContentItem { content_type: string; content_data: string; }
export interface SaveEditRequest { template_id: number; base_id: string; base_name: string; contents: ContentItem[]; }
export interface EditContentResponse { template_id: number; base_id: string; base_name: string; version: number; is_edited: boolean; contents: ContentItem[]; updated_at: string | null; }

export const saveDeclarationEdit = (category: string, data: SaveEditRequest) => client.post(`/v1/declaration-templates/${category}/save`, data);
export const getDeclarationEdit = (category: string, templateId: number, baseId: string) => client.get<EditContentResponse>(`/v1/declaration-templates/${category}/edit/${templateId}/${baseId}`);
export const getDeclarationBaseEdits = (category: string, baseId: string) => client.get(`/v1/declaration-templates/${category}/edits/${baseId}`);

// 下载基地编辑后的文档
export const downloadDeclarationDocument = (category: string, templateId: number, baseId: string) => {
  const token = localStorage.getItem('token');
  // 使用Authorization header而不是token参数
  return fetch(`${client.defaults.baseURL}/v1/declaration-templates/${category}/download/${templateId}/${baseId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }).then(response => {
    if (!response.ok) {
      throw new Error('下载失败');
    }
    return response.blob();
  }).then(blob => {
    const url = window.URL.createObjectURL(blob);
    return url;
  });
};

// ============ 标准项刷新模板接口 ============

export interface StandardTemplate {
  template: { id: number; name: string; document_type: string; file_path: string; status: string; created_at: string; updated_at: string };
  parsed_content: { content_type: string; content_data: string }[];
  template_info: { paragraphs_count?: number; tables_count?: number; sections_count?: number; sheets?: string[]; sheet_details?: Record<string, { columns: string[]; row_count: number }>; error?: string };
}

export const uploadStandardTemplate = (formData: FormData) =>
  client.post<StandardTemplate>('/v1/standard-templates/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
export const getStandardTemplates = () => client.get('/v1/standard-templates');
export const deleteStandardTemplate = (templateId: number) => client.delete(`/v1/standard-templates/${templateId}`);

// 标准项刷新 - 基地用户编辑保存
export const saveStandardEdit = (data: SaveEditRequest) => client.post('/v1/standard-templates/save', data);
export const getStandardEdit = (templateId: number, baseId: string) => client.get<EditContentResponse>(`/v1/standard-templates/edit/${templateId}/${baseId}`);
export const getStandardBaseEdits = (baseId: string) => client.get(`/v1/standard-templates/edits/${baseId}`);

// ============ 系统接口 ============

export const healthCheck = () => client.get('/health');

// ============ 进度看板接口 ============

export interface DeclarationProgress {
  category: string;
  total: number;
  edited: number;
  progress: number;
}

export interface StandardProgress {
  total: number;
  edited: number;
  progress: number;
}

export interface EvidenceProgress {
  total: number;
  passed: number;
  progress: number;
}

export interface BaseProgress {
  base_id: string;
  base_name: string;
  base_code: string;
  declaration_progress: DeclarationProgress[];
  standard_progress: StandardProgress;
  evidence_progress: EvidenceProgress;
}

export interface ProgressOverview {
  bases: BaseProgress[];
  summary: {
    declaration_templates: Record<string, number>;
    standard_template_count: number;
    total_items: number;
    total_evidence: number;
  };
}

export const getProgressOverview = (baseId?: string) => client.get<ProgressOverview>('/v1/progress/overview', { params: { base_id: baseId } });

// ============ 申报风险识别接口 ============

export interface RiskIdentificationData {
  base_id: string;
  site_name?: string;
  site_ip?: string;
  region_name?: string;
  xinchuang_servers?: number;
  x86_servers?: number;
  dengbao_passed?: string;
  mipin_passed?: string;
  asset_huawei?: string;
  contract_direct?: string;
  exclusive_room?: string;
  l1_huawei_supplier?: string;
  access_compliant?: string;
  is_completed?: boolean;
  current_step?: number;
}

export interface RiskRecord {
  id: string;
  base_id: string;
  base_name?: string;
  user_id: string;
  user_name?: string;
  is_completed: boolean;
  current_step: number;
  site_name?: string;
  site_ip?: string;
  region_name?: string;
  xinchuang_servers?: number;
  x86_servers?: number;
  total_servers?: number;
  xinchuang_ratio?: number;
  server_check?: string;
  xinchuang_check?: string;
  dengbao_passed?: string;
  mipin_passed?: string;
  asset_huawei?: string;
  contract_direct?: string;
  exclusive_room?: string;
  l1_huawei_supplier?: string;
  access_compliant?: string;
  overall_risk?: string;
  risk_items?: string[];
  created_at?: string;
  updated_at?: string;
}

export const checkRiskIdentification = (baseId: string) => client.get(`/v1/risk/check/${baseId}`);
export const getMyRiskRecords = () => client.get('/v1/risk/my');
export const getBaseRiskRecord = (baseId: string) => client.get(`/v1/risk/base/${baseId}`);
export const saveRiskIdentification = (data: RiskIdentificationData) => client.post('/v1/risk', data);
export const getAllRiskRecords = () => client.get('/v1/risk/all');
export const deleteRiskRecord = (recordId: string) => client.delete(`/v1/risk/${recordId}`);

// ============ 证据对比接口 ============
export const uploadEvidenceList = (formData: FormData) => client.post('/v1/evidence/upload-list', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
export const getEvidenceList = () => client.get('/v1/evidence/list');
export const getSampleFileInfo = (sampleName: string) => client.get(`/v1/evidence/sample-info/${encodeURIComponent(sampleName)}`);
export const uploadEvidenceMaterial = (itemId: string, formData: FormData) => client.post(`/v1/evidence/upload-material/${itemId}`, formData);
export const compareEvidence = (itemId: string, baseInfo?: any) => {
  const formData = new FormData();
  if (baseInfo) {
    formData.append('base_info', JSON.stringify(baseInfo));
  }
  // 不要手动设置Content-Type，让浏览器自动设置boundary
  return client.post(`/v1/evidence/compare/${itemId}`, formData);
};
export const auditEvidence = (itemId: string, result: string, diagnosis?: string) => 
  client.post(`/v1/evidence/audit/${itemId}`, null, { params: { result, diagnosis } });

// ============ 敏感信息监测接口 ============
export interface SensitiveItem {
  document_name: string;
  category: string;
  sensitive_type: string;
  keywords: string[];
  keyword_counts: Record<string, number>;
  total_count: number;
  content_preview: string;
}

export interface SensitiveScanResult {
  base_id: string;
  base_name: string;
  total_sensitive_count: number;
  category_counts: Record<string, number>;
  sensitive_items: SensitiveItem[];
  scan_time: string;
}

export const scanSensitiveInfo = (baseId: string) => 
  client.post<SensitiveScanResult>('/v1/sensitive/scan', { base_id: baseId });

export const getSensitiveResults = (baseId: string) =>
  client.get<SensitiveScanResult>(`/v1/sensitive/results/${baseId}`);

// ============ 大模型配置接口 ============
export const getLLMConfig = (userId: string) => client.get(`/v1/llm-config/${userId}`);
export const saveLLMConfig = (userId: string, config: any) => client.post(`/v1/llm-config/${userId}`, config);
export const getProviders = () => client.get('/v1/llm-config/providers/list');

// ============ AI服务接口 ============
export const ragGenerate = (data: any) => client.post('/v1/ai/rag/generate', data);
export const ragChat = (data: any) => client.post('/v1/ai/rag/chat', data);
export const runAgent = (data: any) => client.post('/v1/ai/agent/run', data);
export const getAIStatus = (userId: string) => client.get(`/v1/ai/status?user_id=${userId}`);
