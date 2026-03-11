<script>
	import { onMount } from 'svelte';
	import { t } from '$lib/i18n/index.js';
	import { api } from '$lib/api/client.js';
	import { addLog, addError } from '$lib/stores/logStore.js';
	import { cachedFetch, invalidate } from '$lib/api/cache.js';
	import { status } from '$lib/stores/statusStore.js';
	import { FileText, AlertTriangle, CheckCircle, XCircle, Loader2, Pencil, Sparkles } from 'lucide-svelte';
	import MarkdownContent from '$lib/ui/MarkdownContent.svelte';
	import MdEditor from '$lib/ui/md-editor/MdEditor.svelte';
	import TemplatePicker from '$lib/pages/constitution/TemplatePicker.svelte';

	let data = $state(null);
	let validation = $state(null);
	let validating = $state(false);
	let error = $state('');
	let showEditor = $state(false);
	let editorContent = $state('');
	let showGenerateFromIdea = $state(false);
	let generateIdeaDescription = $state('');
	let generatingFromIdea = $state(false);

	onMount(() => { load(); });

	async function load() {
		try { data = await cachedFetch('constitution', () => api.getConstitution()); }
		catch (e) { error = e.message; addError(e.message, 'constitution'); }
	}

	async function validate() {
		validating = true; validation = null;
		addLog($t('log.validating'));
		try {
			validation = await api.validateConstitution();
			addLog(validation.valid ? $t('log.validation_passed') : $t('log.validation_issues'));
			if (validation.valid) {
				invalidate('status');
				status.set(await api.getStatus());
			}
		} catch (e) { addError(e.message, 'validateConstitution'); error = e.message; }
		validating = false;
	}

	async function saveContent(text) {
		try {
			await api.saveConstitution(text);
			validation = null;
			invalidate('constitution', 'status');
			status.set(await api.getStatus());
			await load();
			addLog($t('editor.doc_saved'));
			showEditor = false;
		} catch (e) { addError(e.message, 'constitutionSave'); throw e; }
	}

	function openPreset(content) {
		editorContent = content;
		showEditor = true;
	}

	function openEditor() {
		editorContent = data?.content || '';
		showEditor = true;
	}

	async function generateFromIdea() {
		const desc = generateIdeaDescription.trim();
		if (!desc) return;
		generatingFromIdea = true;
		addLog($t('log.const_generate_start'));
		try {
			const result = await api.generateConstitutionFromIdea(desc);
			if (result?.success && result?.content) {
				editorContent = result.content;
				showEditor = true;
				showGenerateFromIdea = false;
				generateIdeaDescription = '';
				addLog($t('log.const_generate_done'));
			} else {
				addError(result?.message || 'No content returned', 'constGenerate');
			}
		} catch (e) {
			addError(e.message, 'constGenerate');
		}
		generatingFromIdea = false;
	}
</script>

<div class="main-header">
	<h2><FileText size={24} /> {$t('const.title')}</h2>
	<p>{$t('const.subtitle')}</p>
</div>

{#if error}
	<div class="alert alert-warn"><AlertTriangle size={14} /> {error}</div>
{:else if !data}
	<div class="loading-text"><Loader2 size={14} class="spin" /> {$t('app.loading')}</div>
{:else}
	{#if !data.has_constitution}
		<div class="alert alert-info"><AlertTriangle size={14} /> {$t('const.empty')}</div>
		<p class="const-hint">{$t('const.generate_hint')}</p>
		<div class="btn-group constitution-actions">
			<button type="button" class="btn btn-primary" onclick={() => showGenerateFromIdea = !showGenerateFromIdea}>
				<Sparkles size={14} /> {$t('const.generate_with_ai')}
			</button>
			<button class="btn" onclick={openEditor}>
				<Pencil size={14} /> {$t('editor.edit')}
			</button>
		</div>
		{#if showGenerateFromIdea}
			<div class="generate-from-idea-form constitution-generate-form">
				<textarea
					bind:value={generateIdeaDescription}
					placeholder={$t('const.idea_placeholder')}
					rows="4"
					disabled={generatingFromIdea}
				></textarea>
				<button type="button" class="btn btn-primary" disabled={generatingFromIdea || !generateIdeaDescription.trim()} onclick={generateFromIdea}>
					{#if generatingFromIdea}<Loader2 size={14} class="spin" />{:else}<Sparkles size={14} />{/if}
					{$t('const.generate_btn')}
				</button>
			</div>
		{/if}
		<TemplatePicker onSelect={openPreset} />
	{:else}
		{#if $status?.constitution_validated}
			<div class="alert alert-success"><CheckCircle size={14} /> {$t('const.valid')}</div>
		{/if}
		<div class="btn-group">
			<button type="button" class="btn btn-primary" onclick={() => showGenerateFromIdea = true}>
				<Sparkles size={14} /> {$t('const.generate_with_ai')}
			</button>
			{#if !$status?.constitution_validated}
				<button class="btn btn-primary" disabled={validating} onclick={validate}>
					{#if validating}<Loader2 size={14} class="spin" />{:else}<CheckCircle size={14} />{/if}
					{$t('const.validate')}
				</button>
			{/if}
			<button class="btn" onclick={openEditor}>
				<Pencil size={14} /> {$t('editor.edit')}
			</button>
		</div>
		{#if showGenerateFromIdea}
			<div class="generate-from-idea-card expanded">
				<div class="generate-from-idea-form">
					<textarea
						bind:value={generateIdeaDescription}
						placeholder={$t('const.idea_placeholder')}
						rows="4"
						disabled={generatingFromIdea}
					></textarea>
					<button class="btn btn-primary" disabled={generatingFromIdea || !generateIdeaDescription.trim()} onclick={generateFromIdea}>
						{#if generatingFromIdea}<Loader2 size={14} class="spin" />{:else}<Sparkles size={14} />{/if}
						{$t('const.generate_btn')}
					</button>
				</div>
			</div>
		{/if}
	{/if}

	{#if validation}
		{#if validation.valid && !$status?.constitution_validated}
			<div class="alert alert-success"><CheckCircle size={14} /> {$t('const.valid')}</div>
		{:else if !validation.valid}
			<div class="alert alert-warn"><AlertTriangle size={14} /> {$t('const.invalid')}</div>
		{/if}
		<ul class="check-list">
			{#each Object.entries(validation.checks) as [section, ok]}
				<li>
					{#if ok}<CheckCircle size={14} color="var(--gn-bright)" />{:else}<XCircle size={14} color="var(--rd)" />{/if}
					{section.replace(/_/g, ' ')}
				</li>
			{/each}
		</ul>
	{/if}

	{#if data.content}
        <MarkdownContent content={data.content} />
	{/if}

	{#if showEditor}
		<MdEditor
			content={editorContent}
			onSave={saveContent}
			onClose={() => showEditor = false}
		/>
	{/if}
{/if}

<style>
	.const-hint {
		color: var(--dm);
		font-size: 0.875rem;
		margin-bottom: 0.75rem;
	}
	.constitution-actions {
		margin-bottom: 0.75rem;
	}
	.constitution-generate-form {
		margin-bottom: 1.25rem;
	}
	.generate-from-idea-card {
		margin-bottom: 1rem;
	}
	.generate-from-idea-card.expanded {
		margin-top: 0.75rem;
	}
	.generate-from-idea-form {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-top: 0.5rem;
		padding: 0.75rem;
		background: var(--sf);
		border: 0.0625rem solid var(--bd);
		border-radius: var(--r);
	}
	.generate-from-idea-form textarea {
		width: 100%;
		resize: vertical;
		min-height: 5rem;
		padding: 0.5rem;
		border-radius: var(--r);
		border: 0.0625rem solid var(--bd);
		background: var(--bg);
		color: var(--fg);
	}
</style>
