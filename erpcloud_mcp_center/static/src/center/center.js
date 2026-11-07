/** @odoo-module **/

import { Component, onWillStart, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

const paths = {
    bootstrap: "/erpcloud_mcp_center/bootstrap",
    issue: "/erpcloud_mcp_center/issue",
    revoke: "/erpcloud_mcp_center/revoke",
    rotate: "/erpcloud_mcp_center/rotate",
    search: "/erpcloud_mcp_center/search",
    propose: "/erpcloud_mcp_center/propose",
    decide: "/erpcloud_mcp_center/decide",
};

export class MCPCenter extends Component {
    static template = "erpcloud_mcp_center.Main";
    setup() {
        this.notification = useService("notification");
        this.state = proxy({
            tab: "home", loading: true, busy: false, data: null, secret: "", secretVisible: false,
            language: localStorage.getItem("erpcloud_mcp_center_lang") || "vi", platform: "claude",
            keyName: localStorage.getItem("erpcloud_mcp_center_lang") === "en" ? "My assistant" : "Trợ lý của tôi", scope: "read", days: 30,
            partnerQuery: "", productQuery: "", partners: [], products: [], partner: null,
            lineProduct: null, quantity: 1, lines: [], note: "", chosenKey: null, selfTest: "",
        });
        onWillStart(() => this.refresh());
    }
    tr(vi, en) { return this.state.language === "vi" ? vi : en; }
    async call(name, params = {}) { return await rpc(paths[name], params); }
    async refresh() {
        this.state.loading = true;
        try { this.state.data = await this.call("bootstrap"); }
        catch (e) { this.error(e); }
        finally { this.state.loading = false; }
    }
    error(e) { this.notification.add(e?.message || String(e), { type: "danger" }); }
    success(message) { this.notification.add(message, { type: "success" }); }
    setTab(tab) { this.state.tab = tab; this.state.secret = ""; this.state.secretVisible = false; }
    setLanguage() {
        this.state.language = this.state.language === "vi" ? "en" : "vi";
        if (this.state.keyName === "Trợ lý của tôi" || this.state.keyName === "My assistant") {
            this.state.keyName = this.state.language === "vi" ? "Trợ lý của tôi" : "My assistant";
        }
        localStorage.setItem("erpcloud_mcp_center_lang", this.state.language);
    }
    async copy(value) {
        try { await navigator.clipboard.writeText(value); this.success(this.tr("Đã sao chép", "Copied")); }
        catch (e) { this.error(e); }
    }
    get activeKeys() { return (this.state.data?.keys || []).filter((key) => key.active); }
    get pending() { return (this.state.data?.proposals || []).filter((proposal) => proposal.state === "pending"); }
    get selectedKey() {
        return this.activeKeys.find((key) => key.id === Number(this.state.chosenKey)) || this.activeKeys[0];
    }
    get setupText() {
        const url = this.state.data?.url || "https://your-odoo.example/mcp";
        const token = this.state.secret || "<YOUR_PERSONAL_KEY>";
        if (this.state.platform === "codex") {
            return `[mcp_servers.erpcloud]\nurl = "${url}"\nbearer_token_env_var = "ERPCLOUD_MCP_TOKEN"\n\n# Set ERPCLOUD_MCP_TOKEN in your environment to your personal key.`;
        }
        if (this.state.platform === "cursor") {
            return JSON.stringify({ mcpServers: { erpcloud: { url, headers: { Authorization: `Bearer ${token}` } } } }, null, 2);
        }
        if (this.state.platform === "chatgpt") {
            return this.tr("Trong ChatGPT: Plugins → Add custom MCP server. Dán URL HTTPS công khai ở trên; chọn OAuth, tạo plugin và duyệt các công cụ được tìm thấy. Tính năng phụ thuộc gói và quyền workspace.", "In ChatGPT: Plugins → Add custom MCP server. Paste the public HTTPS URL above; choose OAuth, create the plugin and review discovered tools. Availability depends on your plan and workspace permissions.");
        }
        return this.tr("Trong Claude: Settings → Connectors → Add custom connector. Dán URL MCP bên trên và kết nối bằng OAuth. Nếu công cụ của bạn hỗ trợ Bearer key, dùng khóa cá nhân chỉ hiện một lần.", "In Claude: Settings → Connectors → Add custom connector. Paste the MCP URL and connect with OAuth. If your client supports a Bearer key, use the personal key shown once.");
    }
    get assistantBrief() {
        return this.tr(
            `Tôi dùng ERPCloud MCP Center với Odoo. Nếu ứng dụng của bạn hỗ trợ MCP, tôi sẽ thêm máy chủ ${this.state.data?.url || "<MCP_URL>"} bằng giao diện kết nối của ứng dụng và tự đăng nhập/cấp quyền. Sau khi kết nối, hãy dùng công cụ tra cứu khách, sản phẩm và tóm tắt báo giá; mọi câu trả lời về chứng từ cần kèm số và link Odoo. Nếu tôi nhờ lập báo giá, hãy gửi đề xuất để người có quyền duyệt trong MCP Center. Không tự xác nhận hoặc gửi báo giá.`,
            `I use ERPCloud MCP Center with Odoo. If your app supports MCP, I will add ${this.state.data?.url || "<MCP_URL>"} through the app's connector UI and authorize it myself. Once connected, use customer and product lookups plus the sales briefing; include Odoo document numbers and links. For a quotation, submit a proposal for a human approver in MCP Center. Never confirm or send it automatically.`
        );
    }
    async issue() {
        if (this.state.busy) return;
        this.state.busy = true;
        try {
            const result = await this.call("issue", { name: this.state.keyName, scope: this.state.scope, days: Number(this.state.days) });
            await this.refresh();
            this.state.secret = result.secret;
            this.state.secretVisible = false;
            this.state.selfTest = "";
            this.state.chosenKey = result.key.id;
            this.success(this.tr("Đã tạo kết nối. Hãy lưu khóa ngay.", "Connection created. Save the key now."));
        } catch (e) { this.error(e); }
        finally { this.state.busy = false; }
    }
    async testConnection() {
        if (!this.state.secret) return;
        this.state.selfTest = this.tr("Đang kiểm tra…", "Checking…");
        try {
            const headers = { "Content-Type": "application/json", "Accept": "application/json, text/event-stream", "Authorization": `Bearer ${this.state.secret}` };
            const init = await fetch(this.state.data.url, { method: "POST", headers,
                body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "initialize", params: {
                    protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "ERPCloud Center Test", version: "1.0" },
                } }) });
            const first = await init.json();
            if (!init.ok || first.error) throw new Error(first.error?.message || `HTTP ${init.status}`);
            const session = init.headers.get("Mcp-Session-Id");
            if (!session) throw new Error("MCP session missing");
            headers["Mcp-Session-Id"] = session;
            const ready = await fetch(this.state.data.url, { method: "POST", headers,
                body: JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" }) });
            if (!ready.ok) throw new Error(`HTTP ${ready.status}`);
            const tools = await fetch(this.state.data.url, { method: "POST", headers,
                body: JSON.stringify({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} }) });
            const listed = await tools.json();
            if (!tools.ok || listed.error || !Array.isArray(listed.result?.tools)) throw new Error(listed.error?.message || `HTTP ${tools.status}`);
            this.state.selfTest = this.tr(`Kết nối thành công · ${listed.result.tools.length} tiện ích`, `Connected · ${listed.result.tools.length} tools`);
            await this.refresh();
        } catch (e) { this.state.selfTest = this.tr("Kiểm tra thất bại: ", "Test failed: ") + (e?.message || String(e)); }
    }
    async changeKey(key, mode) {
        if (this.state.busy || !window.confirm(this.tr(mode === "revoke" ? "Ngắt kết nối này?" : "Đổi khóa và vô hiệu hóa khóa cũ?", mode === "revoke" ? "Disconnect this key?" : "Rotate and disable the old key?"))) return;
        this.state.busy = true;
        try {
            const result = await this.call(mode, { key_id: key.id });
            await this.refresh();
            if (result.secret) { this.state.secret = result.secret; this.state.chosenKey = result.key.id; }
            this.success(this.tr("Đã cập nhật kết nối", "Connection updated"));
        } catch (e) { this.error(e); }
        finally { this.state.busy = false; }
    }
    async lookup(kind) {
        const query = kind === "partner" ? this.state.partnerQuery : this.state.productQuery;
        if (query.trim().length < 2) { this.state[kind === "partner" ? "partners" : "products"] = []; return; }
        try { this.state[kind === "partner" ? "partners" : "products"] = await this.call("search", { kind, query }); }
        catch (e) { this.error(e); }
    }
    select(kind, row) {
        this.state[kind] = row;
        this.state[kind === "partner" ? "partners" : "products"] = [];
        this.state[kind === "partner" ? "partnerQuery" : "productQuery"] = row.name;
    }
    addLine() {
        if (!this.state.product || !Number.isFinite(Number(this.state.quantity)) || Number(this.state.quantity) <= 0) return;
        this.state.lines.push({ product_id: this.state.product.id, product: this.state.product.name, quantity: Number(this.state.quantity) });
        this.state.product = null; this.state.productQuery = ""; this.state.quantity = 1;
    }
    async propose() {
        if (!this.state.partner || !this.state.lines.length || !this.selectedKey || this.selectedKey.scope !== "quote") return;
        this.state.busy = true;
        try {
            await this.call("propose", { key_id: this.selectedKey.id, partner_id: this.state.partner.id,
                lines: this.state.lines.map(({ product_id, quantity }) => ({ product_id, quantity })), note: this.state.note });
            this.state.lines = []; this.state.note = ""; await this.refresh(); this.setTab("approvals");
            this.success(this.tr("Đã gửi bản xem trước để duyệt", "Preview sent for approval"));
        } catch (e) { this.error(e); }
        finally { this.state.busy = false; }
    }
    async decide(proposal, approve) {
        if (this.state.busy || !window.confirm(this.tr(approve ? "Duyệt và tạo báo giá nháp?" : "Từ chối đề xuất này?", approve ? "Approve and create a draft quotation?" : "Reject this proposal?"))) return;
        this.state.busy = true;
        try {
            const result = await this.call("decide", { proposal_id: proposal.id, approve });
            await this.refresh();
            this.success(this.tr("Đã xử lý đề xuất", "Proposal processed"));
            if (result.order_url) window.open(result.order_url, "_blank", "noopener");
        } catch (e) { this.error(e); }
        finally { this.state.busy = false; }
    }
}

registry.category("actions").add("erpcloud_mcp_center.main", MCPCenter);
