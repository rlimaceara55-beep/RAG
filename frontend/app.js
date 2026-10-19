// Estado Global da Aplicação
let currentQueryInspectionData = null;
let lastIngestionData = null;

document.addEventListener("DOMContentLoaded", () => {
    checkSystemStatus();
    loadAvailableBases();
});

// 1. Verificação de Status do Sistema
async function checkSystemStatus() {
    try {
        const res = await fetch("/api/health");
        const data = await res.json();
        
        // Supabase status
        const supabaseBadge = document.getElementById("badge-supabase");
        const supabaseDot = document.querySelector("#status-supabase .status-dot");
        if (data.supabase && data.supabase.connected) {
            supabaseBadge.textContent = "Conectado";
            supabaseBadge.className = "status-badge success";
            supabaseDot.className = "status-dot success";
        } else {
            supabaseBadge.textContent = "Pendente .env";
            supabaseBadge.className = "status-badge warning";
            supabaseDot.className = "status-dot warning";
        }

        // OpenRouter status
        const openrouterBadge = document.getElementById("badge-openrouter");
        const openrouterDot = document.querySelector("#status-openrouter .status-dot");
        if (data.openrouter && data.openrouter.configured) {
            openrouterBadge.textContent = "Configurado";
            openrouterBadge.className = "status-badge success";
            openrouterDot.className = "status-dot success";
        } else {
            openrouterBadge.textContent = "Pendente .env";
            openrouterBadge.className = "status-badge warning";
            openrouterDot.className = "status-dot warning";
        }
    } catch (err) {
        console.warn("Erro ao verificar healthcheck:", err);
    }
}

// 2. Carrega as Bases Disponíveis no Dropdown
async function loadAvailableBases() {
    try {
        const res = await fetch("/api/query/documents");
        const data = await res.json();
        const select = document.getElementById("select-base");
        
        // Mantém a opção padrão
        select.innerHTML = '<option value="">Todas as Notas Fiscais (Global)</option>';
        
        if (data.documents && data.documents.length > 0) {
            data.documents.forEach(doc => {
                const opt = document.createElement("option");
                opt.value = doc.id;
                opt.textContent = `${doc.numero_nota} — ${doc.fornecedor || 'Fornecedor'} (R$ ${Number(doc.valor_total || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})})`;
                select.appendChild(opt);
            });
        }
    } catch (err) {
        console.warn("Erro ao listar bases:", err);
    }
}

function onBaseSelectionChanged() {
    const select = document.getElementById("select-base");
    const val = select.options[select.selectedIndex].text;
    console.log("Base selecionada:", val);
}

// 3. Alternância de Visualizações
function switchView(viewName) {
    document.querySelectorAll(".view-section").forEach(v => v.classList.remove("active"));
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    
    if (viewName === "chat") {
        document.getElementById("view-chat").classList.add("active");
        document.getElementById("nav-chat-btn").classList.add("active");
    } else {
        document.getElementById("view-ingest").classList.add("active");
        document.getElementById("nav-ingest-btn").classList.add("active");
    }
}

// 4. Execução de Pergunta RAG
async function handleSendQuery(e) {
    e.preventDefault();
    const input = document.getElementById("query-input");
    const queryText = input.value.trim();
    if (!queryText) return;
    
    input.value = "";
    const baseId = document.getElementById("select-base").value;
    
    // Adiciona mensagem do usuário na tela
    appendUserMessage(queryText);
    
    // Animação das etapas do pipeline de consulta
    animateQueryPipelineStart();

    try {
        const res = await fetch("/api/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                pergunta: queryText,
                base_id: baseId || null
            })
        });

        const data = await res.json();
        animateQueryPipelineComplete(data);
        
        appendAssistantMessage(data);
    } catch (err) {
        animateQueryPipelineError(err.message);
        appendErrorMessage("Falha ao comunicar com o servidor: " + err.message);
    }
}

function appendUserMessage(text) {
    const list = document.getElementById("chat-messages");
    const msg = document.createElement("div");
    msg.className = "message user-message";
    msg.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-body">
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    list.appendChild(msg);
    list.scrollTop = list.scrollHeight;
}

function appendAssistantMessage(data) {
    const list = document.getElementById("chat-messages");
    const msg = document.createElement("div");
    msg.className = "message assistant-message";
    
    const isNoData = data.resposta_final === "Sem dados disponiveis na base";
    const inspectionId = "insp_" + Date.now();
    
    // Salva globalmente para inspeção no modal
    window[inspectionId] = data;

    let retrievalInfo = "";
    if (data.pipeline && data.pipeline.retrieval) {
        const total = data.pipeline.retrieval.total_encontrados || 0;
        retrievalInfo = `Recuperados: <strong>${total}</strong> chunks (top_k=5)`;
    }

    msg.innerHTML = `
        <div class="message-avatar">⚡</div>
        <div class="message-body">
            <div class="answer-content">
                ${isNoData ? '<span class="status-badge warning">AUSÊNCIA DE DADOS</span>' : ''}
                <p style="white-space: pre-wrap; font-size: 14px; margin-top: 4px;">${escapeHtml(data.resposta_final)}</p>
            </div>
            
            <div class="rag-inspector-trigger">
                <span style="font-size: 11px; color: var(--text-muted);">${retrievalInfo}</span>
                <button class="btn-inspect" onclick="openRagModalFromData('${inspectionId}')">
                    🔬 Ver Pipeline RAG Detalhado
                </button>
            </div>
        </div>
    `;
    list.appendChild(msg);
    list.scrollTop = list.scrollHeight;
}

function appendErrorMessage(text) {
    const list = document.getElementById("chat-messages");
    const msg = document.createElement("div");
    msg.className = "message assistant-message";
    msg.innerHTML = `
        <div class="message-avatar">⚠️</div>
        <div class="message-body" style="border-color: var(--danger);">
            <p style="color: var(--danger);">${escapeHtml(text)}</p>
        </div>
    `;
    list.appendChild(msg);
    list.scrollTop = list.scrollHeight;
}

function applyExampleQuery(queryText) {
    document.getElementById("query-input").value = queryText;
    document.getElementById("chat-form").dispatchEvent(new Event("submit"));
}

// 5. Controle visual dos passos do pipeline de Consulta
function animateQueryPipelineStart() {
    const steps = [1, 2, 3, 4, 5, 6];
    steps.forEach(s => {
        const el = document.getElementById(`q-step-${s}`);
        el.className = "step-card";
    });
    
    document.getElementById("q-step-1").classList.add("completed");
    document.getElementById("q-step-2").classList.add("active");
    document.getElementById("query-pipeline-status").textContent = "Tokenizando e gerando embedding...";
}

function animateQueryPipelineComplete(data) {
    const steps = [1, 2, 3, 4, 5, 6];
    steps.forEach(s => {
        const el = document.getElementById(`q-step-${s}`);
        el.className = "step-card completed";
    });

    if (data.resposta_final === "Sem dados disponiveis na base") {
        document.getElementById("q-step-5").className = "step-card";
        document.getElementById("q-step-6").className = "step-card";
        document.getElementById("query-pipeline-status").textContent = "Finalizado: Sem dados relevantes (LLM poupado)";
    } else {
        document.getElementById("query-pipeline-status").textContent = "Consulta RAG concluída com sucesso!";
    }
}

function animateQueryPipelineError(msg) {
    document.getElementById("query-pipeline-status").textContent = "Erro: " + msg;
    document.querySelectorAll(".query-pipeline .step-card.active").forEach(el => {
        el.className = "step-card error";
    });
}

// 6. Ingestão de Documentos (Amostras ou Upload)
async function processSampleInvoice(sampleFilename) {
    switchView("ingest");
    animateIngestPipelineStart();
    
    try {
        const res = await fetch("/api/ingest/process-sample", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sample_filename: sampleFilename })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Erro no processamento");

        animateIngestPipelineComplete(data);
        renderIngestionObservability(data);
        loadAvailableBases();
        checkSystemStatus();
    } catch (err) {
        animateIngestPipelineError(err.message);
        alert("Erro ao ingerir: " + err.message);
    }
}

async function ingestAllSamples() {
    const samples = ["NF-1001.pdf", "NF-1002.pdf", "NF-1003.pdf", "NF-1004.pdf"];
    for (const s of samples) {
        await processSampleInvoice(s);
    }
    alert("Todas as 4 notas fiscais de teste foram processadas com sucesso!");
}

async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    animateIngestPipelineStart();
    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/ingest/upload", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Erro no upload");

        animateIngestPipelineComplete(data);
        renderIngestionObservability(data);
        loadAvailableBases();
        checkSystemStatus();
    } catch (err) {
        animateIngestPipelineError(err.message);
        alert("Erro no upload: " + err.message);
    }
}

function animateIngestPipelineStart() {
    const steps = [1, 2, 3, 4, 5, 6];
    steps.forEach(s => {
        const el = document.getElementById(`i-step-${s}`);
        el.className = "step-card";
    });
    document.getElementById("i-step-1").classList.add("active");
    document.getElementById("ingest-pipeline-status").textContent = "Processando OCR e extração digital...";
}

function animateIngestPipelineComplete(data) {
    const steps = [1, 2, 3, 4, 5, 6];
    steps.forEach(s => {
        const el = document.getElementById(`i-step-${s}`);
        el.className = "step-card completed";
    });
    document.getElementById("ingest-pipeline-status").textContent = "Ingestão e Indexação concluídas!";
}

function animateIngestPipelineError(msg) {
    document.getElementById("ingest-pipeline-status").textContent = "Erro na ingestão: " + msg;
    document.querySelectorAll(".ingest-pipeline .step-card.active").forEach(el => {
        el.className = "step-card error";
    });
}

// 7. Renderização do Painel de Observabilidade da Ingestão
function renderIngestionObservability(data) {
    lastIngestionData = data;
    const panel = document.getElementById("ingest-observability-panel");
    panel.style.display = "flex";

    const p = data.pipeline;
    // Tab OCR
    document.getElementById("obs-ocr-content").textContent = 
        `Método: ${p.extracao_ocr.metodo}\nPáginas: ${p.extracao_ocr.paginas}\nCaracteres: ${p.extracao_ocr.caracteres_extraidos}\n\n--- TEXTO EXTRAÍDO ---\n${p.extracao_ocr.raw_text_preview}`;

    // Tab Tabular
    const tabData = p.estruturacao_tabular.dados;
    let itemsHtml = (tabData.itens || []).map(it => `
        <tr>
            <td style="padding:6px; border:1px solid #334155;">${it.produto}</td>
            <td style="padding:6px; border:1px solid #334155; text-align:center;">${it.quantidade}</td>
            <td style="padding:6px; border:1px solid #334155; text-align:right;">R$ ${it.valor_unitario.toFixed(2)}</td>
            <td style="padding:6px; border:1px solid #334155; text-align:right;">R$ ${it.valor_total.toFixed(2)}</td>
        </tr>
    `).join("");

    document.getElementById("obs-tabular-content").innerHTML = `
        <div style="font-size:13px; margin-bottom:12px; line-height:1.6;">
            <strong>Nota Fiscal:</strong> ${tabData.numero_nota} | <strong>Data:</strong> ${tabData.data_emissao}<br/>
            <strong>Fornecedor:</strong> ${tabData.fornecedor} (CNPJ: ${tabData.cnpj})<br/>
            <strong>Cliente:</strong> ${tabData.cliente}<br/>
            <strong>Valor Total:</strong> <span style="color:#10B981; font-weight:700;">R$ ${tabData.valor_total.toFixed(2)}</span>
        </div>
        <table style="width:100%; border-collapse:collapse; font-size:12px;">
            <thead>
                <tr style="background:#1E293B;">
                    <th style="padding:6px; border:1px solid #334155; text-align:left;">Produto/Serviço</th>
                    <th style="padding:6px; border:1px solid #334155;">Qtd</th>
                    <th style="padding:6px; border:1px solid #334155; text-align:right;">Unitário</th>
                    <th style="padding:6px; border:1px solid #334155; text-align:right;">Total</th>
                </tr>
            </thead>
            <tbody>${itemsHtml}</tbody>
        </table>
    `;

    // Tab Chunks
    document.getElementById("obs-chunks-content").innerHTML = p.chunking.chunks.map(c => `
        <div class="chunk-card">
            <div class="chunk-card-header">
                <span>CHUNK #${c.chunk_index} — Seção: ${c.secao}</span>
            </div>
            <div class="chunk-card-body">${escapeHtml(c.conteudo)}</div>
        </div>
    `).join("");

    // Tab Tokens
    document.getElementById("obs-tokens-content").innerHTML = `
        <div style="margin-bottom:10px; font-size:13px;">Total de Tokens no Documento: <strong>${p.tokenizacao.total_tokens_documento}</strong> (cl100k_base)</div>
        ${p.tokenizacao.detalhes.map(d => `
            <div style="margin-bottom:12px;">
                <div style="font-size:11px; color:#A5B4FC; margin-bottom:4px;">Chunk #${d.chunk_index} (${d.token_count} tokens):</div>
                <div class="tokens-badge-cloud">
                    ${d.preview_tokens.map(t => `<span class="token-chip" title="Token ID: ${t.id}">${escapeHtml(t.text)}</span>`).join("")}
                </div>
            </div>
        `).join("")}
    `;

    // Tab Vectors
    document.getElementById("obs-vectors-content").innerHTML = `
        <div style="margin-bottom:10px; font-size:13px;">Modelo: <strong>${p.embedding.modelo}</strong> (${p.embedding.dimensao} dimensões)</div>
        ${p.embedding.amostras.map(a => `
            <div style="margin-bottom:8px; font-family:var(--font-mono); font-size:11px; color:#94A3B8;">
                <strong>Chunk #${a.chunk_index}:</strong> [${a.preview_vetor.join(", ")}, ...]
            </div>
        `).join("")}
    `;
}

function switchDetailTab(tabId) {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    event.target.classList.add("active");
    document.getElementById(tabId).classList.add("active");
}

// 8. Modais de Observabilidade RAG
function openRagModalFromData(dataKey) {
    const data = window[dataKey];
    if (!data) return;

    const modal = document.getElementById("rag-modal");
    const body = document.getElementById("rag-modal-body");
    const p = data.pipeline;

    // Constrói os cards dos 5 candidatos
    const candidates = p.retrieval ? p.retrieval.candidatos_recuperados || [] : [];
    let candidatesHtml = "";
    if (candidates.length === 0) {
        candidatesHtml = `<div class="status-badge warning" style="padding:10px;">Nenhum candidato atingiu a nota mínima de similaridade. Regra ativada: "Sem dados disponiveis na base".</div>`;
    } else {
        candidatesHtml = candidates.map(c => `
            <div class="candidate-item">
                <div class="candidate-header">
                    <span class="candidate-rank">#${c.rank} — Nota Fiscal: ${c.numero_nota} (Chunk #${c.chunk_index})</span>
                    <span class="candidate-score">Score: ${c.score}</span>
                </div>
                <div class="candidate-text">${escapeHtml(c.conteudo)}</div>
            </div>
        `).join("");
    }

    // Token pieces
    const tokens = p.tokenizacao ? p.tokenizacao.preview_tokens || [] : [];
    const tokensHtml = tokens.map(t => `<span class="token-chip">${escapeHtml(t.text)}</span>`).join("");

    body.innerHTML = `
        <div>
            <h4 style="font-size:13px; color:#A5B4FC; margin-bottom:4px;">1. PERGUNTA & TOKENIZAÇÃO</h4>
            <p style="font-size:14px; margin-bottom:8px;"><strong>"${escapeHtml(p.pergunta.texto)}"</strong></p>
            <div style="font-size:11px; color:var(--text-muted); margin-bottom:4px;">Encoding: ${p.tokenizacao.encoding} (${p.tokenizacao.token_count} tokens)</div>
            <div class="tokens-badge-cloud">${tokensHtml}</div>
        </div>

        <hr style="border:none; border-top:1px solid var(--border-color);"/>

        <div>
            <h4 style="font-size:13px; color:#A5B4FC; margin-bottom:4px;">2. EMBEDDING VETORIAL DA PERGUNTA</h4>
            <div style="font-family:var(--font-mono); font-size:11px; color:#94A3B8;">
                Modelo: ${p.embedding.modelo} (384d)<br/>
                Vetor: [${(p.embedding.preview_vetor || []).join(", ")}, ...]
            </div>
        </div>

        <hr style="border:none; border-top:1px solid var(--border-color);"/>

        <div>
            <h4 style="font-size:13px; color:#A5B4FC; margin-bottom:4px;">3. RETRIEVAL — CANDIDATOS RECUPERADOS (top_k=5)</h4>
            <div style="display:flex; flex-direction:column; gap:8px;">
                ${candidatesHtml}
            </div>
        </div>

        <hr style="border:none; border-top:1px solid var(--border-color);"/>

        <div>
            <h4 style="font-size:13px; color:#A5B4FC; margin-bottom:4px;">4. PROMPT AUMENTADO ENVIADO AO LLM</h4>
            <pre class="code-view">${escapeHtml(p.prompt_aumentado.prompt_completo || p.prompt_aumentado.status)}</pre>
        </div>

        <hr style="border:none; border-top:1px solid var(--border-color);"/>

        <div>
            <h4 style="font-size:13px; color:#A5B4FC; margin-bottom:4px;">5. RESPOSTA PRODUZIDA</h4>
            <div style="background:#172133; padding:12px; border-radius:6px; font-size:13px;">
                ${escapeHtml(data.resposta_final)}
            </div>
        </div>
    `;

    modal.style.display = "flex";
}

function closeRagModal() {
    document.getElementById("rag-modal").style.display = "none";
}

async function openDocsModal() {
    const modal = document.getElementById("docs-modal");
    const body = document.getElementById("docs-modal-body");
    modal.style.display = "flex";
    body.innerHTML = "<p>Carregando...</p>";

    try {
        const res = await fetch("/api/query/documents");
        const data = await res.json();
        if (!data.documents || data.documents.length === 0) {
            body.innerHTML = `
                <div style="text-align:center; padding:20px;">
                    <p style="color:var(--text-muted);">Nenhum documento cadastrado no banco Supabase ainda.</p>
                    <p style="margin-top:8px; font-size:12px;">Vá na aba <strong>Ingestão de Dados</strong> para ingerir as Notas Fiscais!</p>
                </div>
            `;
        } else {
            body.innerHTML = data.documents.map(d => `
                <div style="background:#111827; border:1px solid var(--border-color); border-radius:8px; padding:12px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; font-weight:700; color:var(--primary); font-size:13px;">
                        <span>${d.numero_nota}</span>
                        <span style="color:#10B981;">R$ ${Number(d.valor_total || 0).toLocaleString('pt-BR', {minimumFractionDigits:2})}</span>
                    </div>
                    <div style="font-size:12px; color:var(--text-secondary); margin-top:4px;">
                        Fornecedor: <strong>${d.fornecedor || 'N/A'}</strong> (CNPJ: ${d.cnpj || 'N/A'})<br/>
                        Cliente: ${d.cliente || 'N/A'} | Data: ${d.data_emissao || 'N/A'}
                    </div>
                </div>
            `).join("");
        }
    } catch (err) {
        body.innerHTML = `<p style="color:var(--danger);">Erro: ${err.message}</p>`;
    }
}

function closeDocsModal() {
    document.getElementById("docs-modal").style.display = "none";
}

function escapeHtml(text) {
    if (!text) return "";
    return text.toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
