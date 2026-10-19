import json

from rest_framework import serializers

from projects.operation_serializers import DesignOperationSerializer

MAX_INPUT_BYTES = 65_536


class AiInvokeRequestSerializer(serializers.Serializer):
    capability = serializers.CharField(min_length=2, max_length=100)
    tool_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    operation_key = serializers.CharField(min_length=8, max_length=120)
    input_payload = serializers.DictField()

    def validate_input_payload(self, value):
        # Measure the real UTF-8 wire size — ensure_ascii would count the
        # \uXXXX escapes and reject unicode-heavy payloads far below 64 KB.
        encoded = json.dumps(value, default=str, ensure_ascii=False).encode("utf-8")
        if len(encoded) > MAX_INPUT_BYTES:
            raise serializers.ValidationError(
                "input_payload excede el límite de 64 KB."
            )
        return value


class AiInvokeResponseSerializer(serializers.Serializer):
    audit_id = serializers.CharField()
    capability = serializers.CharField()
    model = serializers.CharField()
    output = serializers.CharField()
    tokens_prompt = serializers.IntegerField()
    tokens_completion = serializers.IntegerField()
    latency_ms = serializers.IntegerField()
    credits_debited = serializers.IntegerField()
    test_mode = serializers.BooleanField(required=False)
    usage_id = serializers.UUIDField(required=False, allow_null=True)


class AiAskRequestSerializer(serializers.Serializer):
    surface = serializers.CharField(min_length=2, max_length=40)
    refs = serializers.DictField(required=False)
    question = serializers.CharField(min_length=1, max_length=2000)
    operation_key = serializers.CharField(min_length=8, max_length=120)

    def validate_refs(self, value):
        # Refs are identifiers only — the server resolves them into the typed
        # context itself. Anything else (a nested blob, a payload-shaped
        # object) is not an identity and is refused.
        for key, item in value.items():
            if not isinstance(key, str) or not isinstance(item, (str, int)) or isinstance(item, bool):
                raise serializers.ValidationError(
                    "Las referencias de contexto deben ser identificadores simples."
                )
        return value


class AiAskActionSerializer(serializers.Serializer):
    kind = serializers.CharField()
    path = serializers.CharField()
    label = serializers.CharField()


class AiAskResponseSerializer(serializers.Serializer):
    audit_id = serializers.CharField()
    model = serializers.CharField()
    credits_debited = serializers.IntegerField()
    answer = serializers.CharField()
    actions = AiAskActionSerializer(many=True)
    warnings = serializers.ListField(child=serializers.CharField())


class AiAskTurnSerializer(serializers.Serializer):
    """One durable ask turn — the dock replays these to rebuild the
    conversation for the current context after navigation or reload."""

    question = serializers.CharField()
    answer = AiAskResponseSerializer()
    created_at = serializers.CharField(allow_null=True)


class _RefsDictField(serializers.DictField):
    """Identity refs are name → identifier only — anything payload-shaped is
    not an identity and is refused, mirroring the ask contract."""

    def run_validation(self, data=serializers.empty):
        value = super().run_validation(data)
        for key, item in value.items():
            if not isinstance(key, str) or not isinstance(item, (str, int)) or isinstance(item, bool):
                raise serializers.ValidationError(
                    "Las referencias de contexto deben ser identificadores simples."
                )
        return value


class AiAgentHistorySerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "agent"])
    content = serializers.CharField(min_length=1, max_length=2000)


# The live product payload is a design tree — generous but bounded so a
# bloated document can't push the request body into arbitrary sizes.
MAX_PRODUCT_BYTES = 262144


class _BoundedDictField(serializers.DictField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if len(json.dumps(value, default=str)) > MAX_PRODUCT_BYTES:
            raise serializers.ValidationError("too_large")
        return value


class AiAgentRequestSerializer(serializers.Serializer):
    surface = serializers.CharField(min_length=2, max_length=40)
    refs = _RefsDictField(required=False)
    goal = serializers.CharField(min_length=1, max_length=2000)
    product = _BoundedDictField(required=False)
    # The client's fingerprint of the product payload — persisted on the
    # turn so a restored ops step can refuse to apply onto a changed design.
    product_sig = serializers.CharField(required=False, max_length=64, allow_blank=True)
    history = AiAgentHistorySerializer(many=True, required=False, max_length=6)
    operation_key = serializers.CharField(min_length=8, max_length=120)
    # Conversation identity (popup). Omitted by legacy callers: the server
    # then opens a thread for the run so history stays recoverable.
    thread_id = serializers.UUIDField(required=False, allow_null=True)
    # chat answers and prepares proposals without mutating the domain; work
    # executes the delegated objective under the sealed autonomy.
    interaction_mode = serializers.ChoiceField(choices=["chat", "work"], required=False, default="work")
    attachment_ids = serializers.ListField(child=serializers.UUIDField(), required=False, max_length=6)
    # Effective policy, sealed per run (a preference change governs only new
    # tasks): «propose» Solo proponer — zero domain mutations; «approve» Con
    # aprobación — prepare the coherent set and apply after one approval of
    # the result; «draft» Omitir todo — execute every reversible change
    # already delegated, verify and present the receipt. Emission, sending,
    # charges, committed purchases, catalog publication and physical release
    # always keep the human action the domain requires.
    autonomy = serializers.ChoiceField(choices=["propose", "approve", "draft"], required=False, default="propose")


class AiAgentStepSerializer(serializers.Serializer):
    kind = serializers.CharField()
    tool = serializers.CharField(required=False)
    label = serializers.CharField()
    path = serializers.CharField(required=False)
    action = serializers.CharField(required=False)
    ops = DesignOperationSerializer(many=True, required=False)
    # §08-WC batch edits: validated ops grouped per position.
    items = serializers.ListField(child=serializers.DictField(), required=False)
    simulation = serializers.JSONField(required=False)
    # The person asked to do it; with drafts allowed the server saved it
    # (applied: operation receipt) or kept it as a proposal (apply_error).
    apply_requested = serializers.BooleanField(required=False)
    applied = serializers.JSONField(required=False)
    apply_error = serializers.CharField(required=False)
    # document_layout: the quotation composition proposed for this work.
    layout = serializers.JSONField(required=False)
    project_id = serializers.UUIDField(required=False)


class ClarifyOptionSerializer(serializers.Serializer):
    label = serializers.CharField()
    value = serializers.CharField()


class ClarifySerializer(serializers.Serializer):
    question = serializers.CharField()
    options = ClarifyOptionSerializer(many=True)


class AiAgentQuerySerializer(serializers.Serializer):
    surface = serializers.CharField()
    tool = serializers.CharField(required=False)
    status = serializers.CharField()


class AiAgentRejectedSerializer(serializers.Serializer):
    op = serializers.CharField(allow_null=True)
    reason = serializers.CharField()


class AiAgentAcceptedSerializer(serializers.Serializer):
    """202 — the run is queued on the durable worker; the client polls the
    job detail for the live transcript and the terminal result."""

    job_id = serializers.UUIDField()
    state = serializers.CharField()
    thread_id = serializers.UUIDField(required=False, allow_null=True)


class AiAgentRunSerializer(serializers.Serializer):
    """Durable-job payload for one agent round (first submit or follow-up)."""

    ai_job_id = serializers.UUIDField()
    mode = serializers.ChoiceField(choices=["new", "resume"])
    interaction_mode = serializers.ChoiceField(choices=["chat", "work"], required=False, default="work")
    attachments = serializers.ListField(child=serializers.DictField(), required=False, max_length=6)
    surface = serializers.CharField(min_length=2, max_length=40)
    refs = serializers.DictField(required=False)
    goal = serializers.CharField(min_length=1, max_length=2000)
    product = serializers.DictField(required=False, allow_null=True)
    history = AiAgentHistorySerializer(many=True, required=False, max_length=24)
    operation_key = serializers.CharField(min_length=8, max_length=200)
    # Retry replays the job's original goal — the marker travels so the
    # transcript turn reads "this was a re-run", not a retyped message.
    replay = serializers.BooleanField(required=False, default=False)
    product_sig = serializers.CharField(required=False, max_length=64, allow_blank=True)
    # Set by the resume path only: its history was rebuilt server-side from
    # the stored transcript, so its numbers may ground a follow-up. A
    # first-run payload's history is client-supplied and never trusted.
    history_trusted = serializers.BooleanField(required=False, default=False)
    # Effective policy, sealed per run (a preference change governs only new
    # tasks): «propose» Solo proponer — zero domain mutations; «approve» Con
    # aprobación — prepare the coherent set and apply after one approval of
    # the result; «draft» Omitir todo — execute every reversible change
    # already delegated, verify and present the receipt. Emission, sending,
    # charges, committed purchases, catalog publication and physical release
    # always keep the human action the domain requires.
    autonomy = serializers.ChoiceField(choices=["propose", "approve", "draft"], required=False, default="propose")


class AiAgentResultSerializer(serializers.Serializer):
    test_mode = serializers.BooleanField(required=False)
    """The payload act() stores on the job's `result` column — the envelope
    fields (audit/job ids, state, transcript) live on the job row itself."""

    model = serializers.CharField()
    credits_debited = serializers.IntegerField()
    reply = serializers.CharField()
    plan = serializers.ListField(child=serializers.DictField())
    claims = serializers.ListField(child=serializers.DictField())
    references = serializers.ListField(child=serializers.CharField())
    questions = serializers.ListField(child=serializers.CharField())
    clarify = ClarifySerializer(required=False, allow_null=True)
    metrics = serializers.JSONField(required=False)
    artifacts = serializers.ListField(child=serializers.DictField())
    steps = AiAgentStepSerializer(many=True)
    queries = AiAgentQuerySerializer(many=True)
    warnings = serializers.ListField(child=serializers.CharField())
    rejected = AiAgentRejectedSerializer(many=True)


class AiJobMessageSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=1, max_length=2000)
    interaction_mode = serializers.ChoiceField(choices=["chat", "work"], required=False, default="work")
    attachment_ids = serializers.ListField(child=serializers.UUIDField(), required=False, max_length=6)
    # Follow-ups carry the position's live product so design ops evaluate
    # the current design — a stored snapshot would go stale between turns.
    product = _BoundedDictField(required=False)
    # And the caller's live context refs — a volatile pointer (e.g. the
    # canvas selection) refreshes what "this" means without re-keying the
    # job, whose stored refs stay stable.
    refs = _RefsDictField(required=False)
    # The client's fingerprint of the product payload — persisted on the
    # turn so a restored ops step can refuse to apply onto a changed design.
    product_sig = serializers.CharField(required=False, max_length=64, allow_blank=True)
    # Effective policy, sealed per run (a preference change governs only new
    # tasks): «propose» Solo proponer — zero domain mutations; «approve» Con
    # aprobación — prepare the coherent set and apply after one approval of
    # the result; «draft» Omitir todo — execute every reversible change
    # already delegated, verify and present the receipt. Emission, sending,
    # charges, committed purchases, catalog publication and physical release
    # always keep the human action the domain requires.
    autonomy = serializers.ChoiceField(choices=["propose", "approve", "draft"], required=False, default="propose")


class AiReceiptObjectSerializer(serializers.Serializer):
    kind = serializers.CharField()
    id = serializers.CharField()
    label = serializers.CharField()
    url = serializers.CharField(allow_null=True)
    status = serializers.ChoiceField(choices=["applied", "proposed", "pending", "blocked", "undone"])
    cause = serializers.CharField(allow_null=True)
    operation_id = serializers.CharField(allow_null=True)


class AiReceiptCheckSerializer(serializers.Serializer):
    name = serializers.CharField()
    label = serializers.CharField()
    passed = serializers.BooleanField()
    detail = serializers.CharField(allow_blank=True)


class AiReceiptSerializer(serializers.Serializer):
    """Final receipt of a run: the outcome is decided by typed postconditions
    over saved objects — never by having received provider text."""

    outcome = serializers.ChoiceField(choices=["complete", "partial", "proposal", "blocked", "answer"])
    summary = serializers.CharField()
    autonomy = serializers.CharField()
    interaction_mode = serializers.CharField()
    objects = AiReceiptObjectSerializer(many=True)
    checks = AiReceiptCheckSerializer(many=True)
    attachments = serializers.ListField(child=serializers.DictField())
    credits = serializers.IntegerField(allow_null=True)
    checkpoint = serializers.CharField(allow_null=True)


class AiJobSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    surface = serializers.CharField()
    refs = serializers.DictField()
    goal = serializers.CharField()
    state = serializers.CharField()
    cancel_signaled = serializers.BooleanField(required=False)
    plan = serializers.ListField()
    artifacts = serializers.ListField()
    warnings = serializers.ListField()
    result = AiAgentResultSerializer(required=False, allow_null=True)
    error_code = serializers.CharField(required=False, allow_null=True)
    outcomes = serializers.ListField(required=False)
    # Mid-run signal from the worker's job_runs row — the ai_jobs writes
    # commit only when the run finishes, so live progress rides this.
    live = serializers.DictField(required=False, allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(required=False, allow_null=True)
    thread_id = serializers.UUIDField(required=False, allow_null=True)
    interaction_mode = serializers.CharField(required=False, allow_null=True)
    autonomy = serializers.CharField(required=False, allow_null=True)
    receipt = AiReceiptSerializer(required=False, allow_null=True)


class AiJobOutcomeSerializer(serializers.Serializer):
    """Client report: what the human did with one proposed step."""

    turn_index = serializers.IntegerField(min_value=0, max_value=1000)
    step_index = serializers.IntegerField(min_value=0, max_value=1000)
    action = serializers.ChoiceField(
        choices=["applied", "declined", "apply_failed", "undone"]
    )
    ops = serializers.ListField(
        child=serializers.CharField(max_length=80),
        required=False,
        max_length=200,
    )


class AiJobOutcomeResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    recorded = serializers.BooleanField()


class AiMetricsSerializer(serializers.Serializer):
    work = serializers.ListField(child=serializers.DictField(), required=False)
    window_days = serializers.IntegerField()
    jobs = serializers.DictField()
    commands = serializers.DictField()
    approvals = serializers.DictField()
    artifacts_produced = serializers.IntegerField()
    cost = serializers.DictField()
    time_saved = serializers.DictField()


class AiJobDetailSerializer(AiJobSerializer):
    transcript = serializers.ListField()


class AiPresenceQuerySerializer(serializers.Serializer):
    surface = serializers.CharField(min_length=2, max_length=80)
    refs = serializers.CharField(max_length=8000, required=False, default="{}")

    def validate_refs(self, value):
        try:
            decoded = json.loads(value)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Las referencias no son válidas.") from None
        refs = _RefsDictField().run_validation(decoded)
        if len(refs) > 30 or any(len(key) > 80 or not isinstance(value, str) or len(value) > 200 for key, value in refs.items()):
            raise serializers.ValidationError("Las referencias deben ser identificadores breves.")
        return refs


class AiPresenceSerializer(serializers.Serializer):
    context_label = serializers.CharField()
    context_url = serializers.CharField(allow_null=True)
    job = AiJobSerializer(allow_null=True)


class AiAgentResumeRequestSerializer(serializers.Serializer):
    pass


class AiThreadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    interaction_mode = serializers.CharField()
    autonomy = serializers.CharField()
    origin = serializers.CharField()
    archived = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    last_activity_at = serializers.DateTimeField()


class AiThreadListSerializer(serializers.Serializer):
    items = AiThreadSerializer(many=True)
    next_cursor = serializers.CharField(allow_null=True)


class AiThreadQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=120, default="")
    archived = serializers.BooleanField(required=False, default=False)
    cursor = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")


class AiThreadCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=120, default="")
    interaction_mode = serializers.ChoiceField(choices=["chat", "work"], required=False, default="chat")
    autonomy = serializers.ChoiceField(choices=["propose", "approve", "draft"], required=False, default="approve")


class AiThreadUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=120)
    archived = serializers.BooleanField(required=False)
    interaction_mode = serializers.ChoiceField(choices=["chat", "work"], required=False)
    autonomy = serializers.ChoiceField(choices=["propose", "approve", "draft"], required=False)


class AiTimelineEntrySerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["job", "ask"])
    id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    goal = serializers.CharField(allow_null=True)
    state = serializers.CharField(allow_null=True)
    surface = serializers.CharField()
    refs = serializers.DictField()
    interaction_mode = serializers.CharField()
    autonomy = serializers.CharField()
    receipt = AiReceiptSerializer(allow_null=True)
    error_code = serializers.CharField(allow_null=True)
    question = serializers.CharField(allow_null=True)
    answer = serializers.CharField(allow_null=True)


class AiTimelineSerializer(serializers.Serializer):
    items = AiTimelineEntrySerializer(many=True)
    next_cursor = serializers.CharField(allow_null=True)


class AiAttachmentCoverageSerializer(serializers.Serializer):
    unit = serializers.CharField(allow_blank=True)
    total = serializers.IntegerField()
    processed = serializers.IntegerField()
    unprocessed_count = serializers.IntegerField()
    visual_count = serializers.IntegerField()


class AiAttachmentPartSerializer(serializers.Serializer):
    ref = serializers.CharField()
    text = serializers.CharField()


class AiAttachmentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    file_name = serializers.CharField()
    media_type = serializers.CharField()
    kind = serializers.CharField()
    byte_size = serializers.IntegerField()
    file_sha256 = serializers.CharField()
    status = serializers.ChoiceField(choices=["READY", "PARTIAL", "UNREADABLE"])
    thread_id = serializers.UUIDField(allow_null=True)
    coverage = AiAttachmentCoverageSerializer()
    preview = AiAttachmentPartSerializer(many=True)
    created_at = serializers.DateTimeField()


class AiAttachmentDetailSerializer(AiAttachmentSerializer):
    parts = AiAttachmentPartSerializer(many=True)
    visual = serializers.ListField(child=serializers.CharField())
    unprocessed = serializers.ListField(child=serializers.CharField())


class AiAttachmentListSerializer(serializers.Serializer):
    items = AiAttachmentSerializer(many=True)


class AiAttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    thread_id = serializers.UUIDField(required=False, allow_null=True)


class AiAttachmentFormatSerializer(serializers.Serializer):
    kind = serializers.CharField()
    label = serializers.CharField()
    extensions = serializers.ListField(child=serializers.CharField())
    reading = serializers.CharField()
    max_bytes = serializers.IntegerField()


class AiAttachmentMatrixSerializer(serializers.Serializer):
    formats = AiAttachmentFormatSerializer(many=True)
    max_per_turn = serializers.IntegerField()
    max_file_bytes = serializers.IntegerField()
