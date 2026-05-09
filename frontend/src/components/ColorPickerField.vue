<template>
  <div class="color-picker-field">
    <v-text-field
      :label="label"
      :model-value="safeValue"
      :error-messages="errorMessages"
      :hint="hint"
      :disabled="disabled"
      :readonly="disabled"
      :persistent-hint="Boolean(hint)"
      @click="openPicker"
      @click:append-inner="openPicker"
    >
      <template #append-inner>
        <button
          type="button"
          class="color-picker-field__swatch"
          :style="{ backgroundColor: safeValue }"
          :aria-label="label"
          :disabled="disabled"
        />
      </template>
    </v-text-field>
    <input
      ref="inputRef"
      class="color-picker-field__native"
      type="color"
      :value="safeValue"
      :disabled="disabled"
      @input="updateValue"
    >
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

const props = defineProps<{
  modelValue?: string;
  label: string;
  hint?: string;
  errorMessages?: string[] | string;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  (event: "update:modelValue", value: string): void;
}>();

const inputRef = ref<HTMLInputElement | null>(null);

const safeValue = computed(() => {
  const value = (props.modelValue || "").trim();
  return /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(value) ? value : "#f8be27";
});

function openPicker() {
  if (props.disabled) return;
  inputRef.value?.click();
}

function updateValue(event: Event) {
  const target = event.target as HTMLInputElement | null;
  if (!target?.value) return;
  emit("update:modelValue", target.value);
}
</script>

<style scoped>
.color-picker-field {
  position: relative;
}

.color-picker-field__swatch {
  width: 1.4rem;
  height: 1.4rem;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.45);
  cursor: pointer;
}

.color-picker-field__native {
  position: absolute;
  inset: 0;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}
</style>
