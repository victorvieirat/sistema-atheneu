import os
import sys
import re
import json
import argparse
import unicodedata
import difflib

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

try:
    import yaml
except ImportError:
    yaml = None

EXCLUDE_DIRS = {'98_Privado', '.git', '.tmp.driveupload', '.tmp.drivedownload', 'node_modules'}
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}
DOC_EXTS = {'.pdf', '.epub', '.docx', '.xlsx', '.csv', '.zip'}
ATTACHMENT_EXTS = IMAGE_EXTS | DOC_EXTS

def normalize_text(s):
    return unicodedata.normalize('NFC', s)

def clean_heading_for_matching(h):
    # Remove leading hashes, strip formatting like **, *, `, and wikilinks
    h = re.sub(r'^#+\s*', '', h).strip()
    h = re.sub(r'[*`_]', '', h)
    h = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', h)
    return h.strip().lower()

class VaultAuditor:
    def __init__(self, vault_dir='atheneu', config_dir='.obsidian', strict=False):
        self.vault_dir = vault_dir.rstrip('/\\')
        self.config_dir = config_dir.rstrip('/\\')
        self.strict = strict
        
        self.notes = {}            # relpath -> content
        self.all_files = set()     # relpaths of all tracked files
        self.stem_map = {}         # stem -> list of relpaths
        self.attachment_map = {}   # basename -> list of relpaths
        self.base_map = {}         # basename -> relpath
        self.canvas_map = {}       # basename -> relpath
        self.headings = {}         # relpath -> list of cleaned headings
        self.block_ids = {}        # relpath -> set of block ids
        
        self.errors = []
        self.warnings = []
        self.fixes = []

    def log_error(self, path, msg):
        self.errors.append((path, msg))
        print(f"[ERRO] {path}: {msg}")

    def log_warning(self, path, msg):
        self.warnings.append((path, msg))
        print(f"[AVISO] {path}: {msg}")

    def scan_vault(self):
        for dirpath, dirnames, filenames in os.walk(self.vault_dir):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fn in filenames:
                p = os.path.join(dirpath, fn).replace('\\', '/')
                self.all_files.add(p)
                
                # Check unicode normalization of filename
                if unicodedata.normalize('NFC', fn) != fn:
                    self.log_warning(p, "Nome de arquivo não está na forma normalizada NFC (Unicode).")
                
                ext = os.path.splitext(fn)[1].lower()
                base_name = os.path.basename(p)
                stem = os.path.splitext(base_name)[0]
                
                if ext == '.md':
                    with open(p, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.notes[p] = content
                    self.stem_map.setdefault(stem, []).append(p)
                    
                    # Extract headings and block IDs
                    h_list = []
                    b_set = set()
                    for line in content.splitlines():
                        if re.match(r'^#+\s+', line):
                            h_list.append(clean_heading_for_matching(line))
                        # Match block identifiers ^block-id at end of lines
                        bm = re.search(r'\^([a-zA-Z0-9-]+)\s*$', line)
                        if bm:
                            b_set.add(bm.group(1))
                    self.headings[p] = h_list
                    self.block_ids[p] = b_set
                    
                elif ext == '.base':
                    self.base_map[base_name] = p
                    self.stem_map.setdefault(stem, []).append(p)
                elif ext == '.canvas':
                    self.canvas_map[base_name] = p
                    self.stem_map.setdefault(stem, []).append(p)
                elif ext in ATTACHMENT_EXTS:
                    self.attachment_map.setdefault(base_name, []).append(p)

    def check_duplicates_and_stubs(self):
        # 1. Duplicates
        for stem, paths in self.stem_map.items():
            if len(paths) > 1:
                self.log_warning("Geral", f"Stems de arquivos duplicados entre pastas: '{stem}' presente em {paths}")
        
        # 2. Empty / near-empty stubs
        for p, txt in self.notes.items():
            if '_templates' in p:
                continue
            stripped = txt.strip()
            if len(stripped) < 40:
                self.log_warning(p, f"Nota parece ser um stub ou vazia ({len(stripped)} caracteres). Possível criação acidental por clique.")
            if re.search(r'\(\d+\)\.md$|copia|copy|conflict', os.path.basename(p), re.I):
                self.log_warning(p, "Nome de arquivo sugere cópia de conflito ou duplicata automática.")

    def check_obsidian_configs(self):
        if not os.path.exists(self.config_dir):
            return
        
        app_json_path = os.path.join(self.config_dir, 'app.json')
        if os.path.exists(app_json_path):
            with open(app_json_path, 'r', encoding='utf-8') as f:
                app_cfg = json.load(f)
            att_folder = app_cfg.get('attachmentFolderPath')
            if att_folder and not os.path.isdir(att_folder):
                self.log_error(app_json_path, f"Pasta de anexos configurada não existe: '{att_folder}'")
            new_folder = app_cfg.get('newFileFolderPath')
            if new_folder and not os.path.isdir(new_folder):
                self.log_error(app_json_path, f"Pasta de novas notas configurada não existe: '{new_folder}'")
        
        dn_json_path = os.path.join(self.config_dir, 'daily-notes.json')
        if os.path.exists(dn_json_path):
            with open(dn_json_path, 'r', encoding='utf-8') as f:
                dn_cfg = json.load(f)
            dn_folder = dn_cfg.get('folder')
            if dn_folder and not os.path.isdir(dn_folder):
                self.log_error(dn_json_path, f"Pasta de daily-notes configurada não existe: '{dn_folder}'")
            dn_tpl = dn_cfg.get('template')
            if dn_tpl:
                tpl_exists = os.path.isfile(dn_tpl) or os.path.isfile(dn_tpl + '.md')
                if not tpl_exists:
                    self.log_error(dn_json_path, f"Template de daily-notes configurado não existe: '{dn_tpl}'")

    def _validate_wikilink(self, p, context_label, bang, raw_inner, is_template=False):
        template_placeholders = {'MOC_Nome_da_Area', 'Fonte_Exemplo', 'Outra_Nota_do_Jardim', 'Nota_Atomica_1'}
        target_part = raw_inner.split('|', 1)[0].strip()
        subpath = None
        if '#' in target_part:
            note_part, subpath = target_part.split('#', 1)
            note_part = note_part.strip()
        else:
            note_part = target_part

        if not note_part and not subpath:
            self.log_error(p, f"{context_label}: WikiLink vazio '{bang}[[{raw_inner}]]'")
            return

        if is_template and note_part in template_placeholders:
            return

        if '98_Privado' in note_part:
            self.log_error(p, f"{context_label}: Violação de privacidade referenciando 98_Privado: '{note_part}'")
            return

        if note_part.startswith(f"{self.vault_dir}/") or note_part.startswith("atheneu/"):
            self.log_warning(p, f"{context_label}: WikiLink com prefixo de raiz frágil '{note_part}'. Prefira formato curto ('shortest').")

        if '\\' in note_part:
            self.log_warning(p, f"{context_label}: WikiLink contendo barra invertida Windows '\\': '{note_part}'")

        resolved_file = None
        if not note_part:
            resolved_file = p
        elif note_part in self.stem_map:
            resolved_file = self.stem_map[note_part][0]
        elif note_part in self.attachment_map:
            resolved_file = self.attachment_map[note_part][0]
        elif note_part in self.base_map:
            resolved_file = self.base_map[note_part]
        elif note_part in self.canvas_map:
            resolved_file = self.canvas_map[note_part]
        elif note_part in self.all_files:
            resolved_file = note_part
        elif (f"{self.vault_dir}/" + note_part) in self.all_files:
            resolved_file = f"{self.vault_dir}/" + note_part

        if not resolved_file:
            candidates = (
                list(self.stem_map.keys())
                + list(self.attachment_map.keys())
                + list(self.base_map.keys())
                + list(self.canvas_map.keys())
            )
            matches = difflib.get_close_matches(note_part, candidates, n=1, cutoff=0.7)
            hint = f" (Sugestão: '{matches[0]}')" if matches else ""
            self.log_error(p, f"{context_label}: WikiLink não resolvido '{bang}[[{raw_inner}]]'{hint}")
        else:
            if subpath:
                if subpath.startswith('^'):
                    block_clean = subpath.lstrip('^')
                    if resolved_file in self.block_ids and block_clean not in self.block_ids[resolved_file]:
                        self.log_error(p, f"{context_label}: Block ID '^{block_clean}' não encontrado em '{resolved_file}'")
                elif resolved_file.endswith('.base'):
                    if yaml:
                        try:
                            with open(resolved_file, 'r', encoding='utf-8') as bf:
                                b_data = yaml.safe_load(bf)
                            views = [v.get('name') for v in b_data.get('views', []) if isinstance(v, dict)]
                            if subpath not in views:
                                self.log_error(p, f"{context_label}: Visualização '{subpath}' não encontrada no arquivo Base '{resolved_file}'. Views válidas: {views}")
                        except Exception as e:
                            self.log_error(p, f"{context_label}: Erro ao ler base '{resolved_file}': {e}")
                elif resolved_file.endswith('.md'):
                    clean_sub = clean_heading_for_matching(subpath)
                    file_headings = self.headings.get(resolved_file, [])
                    if clean_sub not in file_headings:
                        self.log_error(p, f"{context_label}: Cabeçalho '#{subpath}' não encontrado em '{resolved_file}'")

    def check_wikilinks_and_markdown(self):
        for p, content in self.notes.items():
            is_template = '_templates' in p
            lines = content.splitlines()
            
            # Check unquoted wikilinks in YAML
            fm_m = re.match(r'^---\s*\n(.*?)\n---', content, re.S)
            if fm_m and not is_template:
                yaml_block = fm_m.group(1)
                for line_idx, y_line in enumerate(yaml_block.splitlines(), 2):
                    if '[[' in y_line and not ('"' in y_line or "'" in y_line):
                        self.log_warning(p, f"Linha {line_idx}: WikiLink sem aspas no YAML frontmatter: {y_line.strip()}")
            
            # Check line-by-line for table pipes, IA_CONTEXTO, wikilinks
            in_code_block = False
            for idx, line in enumerate(lines, 1):
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    continue
                
                # Check images missing IA_CONTEXTO in Jardim and Esforcos
                if (p.startswith(f'{self.vault_dir}/03_Jardim/') or p.startswith(f'{self.vault_dir}/05_Esforcos/')) and not is_template:
                    if '![[' in line and '.base' not in line and '.canvas' not in line:
                        subsequent = '\n'.join(lines[idx:idx+4])
                        if '%% IA_CONTEXTO %%' not in subsequent and '%% IA_CONTEXTO' not in subsequent:
                            self.log_warning(p, f"Linha {idx}: Imagem incorporada sem bloco '%% IA_CONTEXTO %%' imediatamente abaixo: {line.strip()}")
                
                # Check wikilinks inside table lines with unescaped pipes
                if line.lstrip().startswith('|'):
                    for wm in re.finditer(r'\[\[([^\]]+)\]\]', line):
                        inner = wm.group(1)
                        if '|' in inner and r'\|' not in inner:
                            self.log_warning(p, f"Linha {idx}: Pipe '|' sem escape em WikiLink dentro de tabela Markdown: [[{inner}]]")

                # Match all [[...]] and ![[...]]
                for m in re.finditer(r'(!?)\[\[([^\]]+)\]\]', line):
                    bang = m.group(1)
                    raw_inner = m.group(2)
                    self._validate_wikilink(p, f"Linha {idx}", bang, raw_inner, is_template=is_template)

    def check_canvas_files(self):
        valid_preset_colors = {'1', '2', '3', '4', '5', '6'}
        valid_node_types = {'text', 'file', 'link', 'group'}

        for base_name, p in self.canvas_map.items():
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                self.log_error(p, f"JSON Canvas inválido ou malformado: {e}")
                continue

            if not isinstance(data, dict):
                self.log_error(p, "Raiz do arquivo .canvas deve ser um objeto JSON.")
                continue

            nodes = data.get('nodes', [])
            edges = data.get('edges', [])
            if not isinstance(nodes, list) or not isinstance(edges, list):
                self.log_error(p, "Campos 'nodes' e 'edges' devem ser listas JSON.")
                continue

            node_ids = set()
            for idx, node in enumerate(nodes):
                if not isinstance(node, dict):
                    self.log_error(p, f"Nó #{idx} não é um objeto JSON.")
                    continue
                nid = node.get('id')
                if not nid or not isinstance(nid, str):
                    self.log_error(p, f"Nó #{idx} sem 'id' string válido.")
                    continue
                if nid in node_ids:
                    self.log_error(p, f"ID de nó duplicado no Canvas: '{nid}'")
                node_ids.add(nid)

                ntype = node.get('type')
                if ntype not in valid_node_types:
                    self.log_error(p, f"Nó '{nid}': tipo inválido '{ntype}' (esperado: {valid_node_types}).")

                color = node.get('color')
                if color is not None:
                    if not (color in valid_preset_colors or re.match(r'^#[0-9a-fA-F]{6}$', str(color))):
                        self.log_error(p, f"Nó '{nid}': cor inválida '{color}'.")

                if ntype == 'file':
                    f_target = str(node.get('file', '')).replace('\\', '/')
                    if not f_target:
                        self.log_error(p, f"Nó '{nid}' (type=file): atributo 'file' vazio.")
                    elif '98_Privado' in f_target:
                        self.log_error(p, f"Nó '{nid}' (type=file): Violação de privacidade referenciando 98_Privado: '{f_target}'")
                    elif f_target not in self.all_files and not os.path.isfile(f_target):
                        self.log_error(p, f"Nó '{nid}' (type=file): Arquivo alvo não existe no cofre: '{f_target}'")

                elif ntype == 'text':
                    txt = node.get('text', '')
                    if not isinstance(txt, str):
                        self.log_error(p, f"Nó '{nid}' (type=text): atributo 'text' não é string.")
                        continue
                    in_code = False
                    for line in txt.splitlines():
                        if line.strip().startswith('```'):
                            in_code = not in_code
                            continue
                        if in_code:
                            continue
                        for m in re.finditer(r'(!?)\[\[([^\]]+)\]\]', line):
                            self._validate_wikilink(p, f"Nó '{nid}'", m.group(1), m.group(2), is_template=False)

            edge_ids = set()
            for idx, edge in enumerate(edges):
                if not isinstance(edge, dict):
                    self.log_error(p, f"Aresta #{idx} não é um objeto JSON.")
                    continue
                eid = edge.get('id')
                if not eid or not isinstance(eid, str):
                    self.log_error(p, f"Aresta #{idx} sem 'id' string válido.")
                elif eid in edge_ids:
                    self.log_error(p, f"ID de aresta duplicado no Canvas: '{eid}'")
                else:
                    edge_ids.add(eid)

                fn = edge.get('fromNode')
                tn = edge.get('toNode')
                if fn not in node_ids:
                    self.log_error(p, f"Aresta '{eid}': fromNode '{fn}' aponta para nó inexistente.")
                if tn not in node_ids:
                    self.log_error(p, f"Aresta '{eid}': toNode '{tn}' aponta para nó inexistente.")

    def check_privacy_and_quartz_compat(self):
        safe_email_patterns = (
            'seu_email', 'example.', 'exemplo.', 'usuario@', 'user@', 'teste@', 'email@'
        )
        cpf_re = re.compile(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b')
        phone_re = re.compile(
            r'(?:\+55\s*\(?\d{2}\)?\s*9?\d{4}-\d{4}|\(\d{2}\)\s*9?\d{4}-\d{4})'
        )
        email_re = re.compile(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b')
        secret_re = re.compile(r'\b(?:AIza[0-9A-Za-z\-_]{35}|ghp_[0-9A-Za-z]{36}|sk-[0-9A-Za-z]{32,})\b')
        private_marker_re = re.compile(r'\b(?:NAO_PUBLICAR|CONFIDENCIAL_PRIVADO)\b')

        for p, content in self.notes.items():
            is_template = '_templates' in p

            # 1. Check unresolved {{...}} placeholders in YAML frontmatter outside templates
            fm_m = re.match(r'^---\s*\n(.*?)\n---', content, re.S)
            if fm_m and not is_template:
                yaml_block = fm_m.group(1)
                if re.search(r'\{\{[^}]+\}\}', yaml_block):
                    self.log_error(
                        p,
                        "Frontmatter YAML contém placeholder '{{...}}' não resolvido (incompatível com o build do Quartz)."
                    )

            # 2. Check balanced %% Obsidian comment delimiters outside code blocks and check PII
            in_code_block = False
            comment_delim_count = 0

            for idx, line in enumerate(content.splitlines(), 1):
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    continue

                line_no_inline_code = re.sub(r'`[^`]*`', '', line)
                comment_delim_count += len(re.findall(r'%%', line_no_inline_code))

                if not is_template and re.match(r'^\s*%%\s*IA_CONTEXTO\s*%%\s*$', line_no_inline_code):
                    self.log_error(
                        p,
                        f"Linha {idx}: '%% IA_CONTEXTO %%' fechado na mesma linha (use '%% IA_CONTEXTO' no início e '%%' ao final do bloco para ocultar a transcrição no Obsidian e no Quartz)."
                    )

                if is_template:
                    continue

                for m in cpf_re.finditer(line):
                    self.log_error(p, f"Linha {idx}: Possível CPF detectado em nota pública: '{m.group(0)}'")

                for m in phone_re.finditer(line):
                    self.log_error(p, f"Linha {idx}: Possível telefone pessoal detectado em nota pública: '{m.group(0)}'")

                for m in email_re.finditer(line):
                    em = m.group(0).lower()
                    if not any(pat in em for pat in safe_email_patterns):
                        self.log_warning(p, f"Linha {idx}: E-mail detectado em nota pública (verifique se não é dado pessoal): '{m.group(0)}'")

                if secret_re.search(line):
                    self.log_error(p, f"Linha {idx}: Possível chave de API ou token secreto detectado.")

                if private_marker_re.search(line):
                    self.log_error(p, f"Linha {idx}: Marcador de conteúdo privado (NAO_PUBLICAR) fora de 98_Privado.")

            if comment_delim_count % 2 != 0:
                self.log_error(
                    p,
                    f"Quantidade ímpar de delimitadores '%%' ({comment_delim_count}). Bloco de comentário não fechado pode vazar ou ocultar texto no Quartz."
                )

    def run_check(self):
        print(f"[INSTRUCAO] Iniciando auditoria de referências locais em '{self.vault_dir}'...")
        self.scan_vault()
        self.check_duplicates_and_stubs()
        self.check_obsidian_configs()
        self.check_wikilinks_and_markdown()
        self.check_canvas_files()
        self.check_privacy_and_quartz_compat()
        
        print("\n" + "="*50)
        print(f"RESUMO DA AUDITORIA: {len(self.errors)} erro(s), {len(self.warnings)} aviso(s)")
        print("="*50)
        
        if self.errors:
            return 1
        if self.strict and self.warnings:
            return 1
        return 0

    def run_fix(self, auto_confirm=False):
        print(f"[INSTRUCAO] Verificando correções automáticas seguras...")
        self.scan_vault()
        
        # Candidate changes: (filepath, old_text, new_text)
        file_changes = {}
        
        for p, content in self.notes.items():
            new_content = content
            
            # 1. Replace fragile [[atheneu/...]] with shortest [[basename]]
            def replace_fragile_wikilink(match):
                prefix = match.group(1) # ! or empty
                inner = match.group(2)
                
                parts = inner.split('|', 1)
                target = parts[0].strip()
                alias = f"|{parts[1]}" if len(parts) > 1 else ""
                
                if target.startswith(f"{self.vault_dir}/") or target.startswith("atheneu/"):
                    base = os.path.basename(target)
                    # verify unambiguous
                    stem = os.path.splitext(base)[0]
                    if base in self.attachment_map and len(self.attachment_map[base]) == 1:
                        return f"{prefix}[[{base}{alias}]]"
                    elif stem in self.stem_map and len(self.stem_map[stem]) == 1:
                        return f"{prefix}[[{stem}{alias}]]"
                return match.group(0)
            
            new_content = re.sub(r'(!?)\[\[([^\]]+)\]\]', replace_fragile_wikilink, new_content)
            
            # 2. Escape table pipes in wikilinks on table lines
            lines = new_content.splitlines()
            changed_lines = False
            for i, line in enumerate(lines):
                if line.lstrip().startswith('|'):
                    def escape_pipe_in_link(m):
                        inner = m.group(1)
                        if '|' in inner and r'\|' not in inner:
                            parts = inner.split('|', 1)
                            return f"[[{parts[0]}\\|{parts[1]}]]"
                        return m.group(0)
                    new_l = re.sub(r'\[\[([^\]]+)\]\]', escape_pipe_in_link, line)
                    if new_l != line:
                        lines[i] = new_l
                        changed_lines = True
            if changed_lines:
                new_content = '\n'.join(lines)
                if content.endswith('\n'):
                    new_content += '\n'
            
            if new_content != content:
                file_changes[p] = new_content
        
        if not file_changes:
            print("[SUCESSO] Nenhuma correção automática necessária. Todas as referências determinísticas estão padronizadas.")
            return 0
        
        print(f"[ARQUIVO] {len(file_changes)} arquivo(s) podem ser normalizados:")
        for p in file_changes:
            print(f"  - {p}")
            
        if not auto_confirm:
            sys.stdout.write("\nDeseja aplicar as correções atômicas em UTF-8? [S/n]: ")
            sys.stdout.flush()
            ans = sys.stdin.readline().strip().lower()
            if ans not in ('s', 'sim', 'y', 'yes', ''):
                print("[INFO] Operação cancelada pelo usuário.")
                return 0
        
        # Apply atomically via .tmp and os.replace
        for p, new_txt in file_changes.items():
            tmp_path = p + '.tmp'
            with open(tmp_path, 'w', encoding='utf-8') as f:
                f.write(new_txt)
            os.replace(tmp_path, p)
            print(f"[SUCESSO] Atualizado atomicamente: {p}")
            
        return 0

def main():
    parser = argparse.ArgumentParser(description="Auditor e Corretor de Referências Locais do Obsidian para Sistema Atheneu")
    parser.add_argument('--vault', default='atheneu', help="Diretório raiz do conteúdo do cofre (padrão: atheneu)")
    parser.add_argument('--config-dir', default='.obsidian', help="Diretório de configurações do Obsidian (padrão: .obsidian)")
    parser.add_argument('--check', action='store_true', default=True, help="Modo somente leitura de verificação (padrão)")
    parser.add_argument('--fix', action='store_true', help="Aplica correções automáticas seguras e determinísticas")
    parser.add_argument('-y', '--yes', action='store_true', help="Modo autônomo (não solicita confirmação interativa)")
    parser.add_argument('--strict', action='store_true', help="Retorna código de erro 1 se houver avisos")
    
    args = parser.parse_args()
    auditor = VaultAuditor(vault_dir=args.vault, config_dir=args.config_dir, strict=args.strict)
    
    if args.fix:
        exit_code = auditor.run_fix(auto_confirm=args.yes)
    else:
        exit_code = auditor.run_check()
        
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
