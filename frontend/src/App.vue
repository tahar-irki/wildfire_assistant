<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import {
  sendChatMessage,
  checkBackendHealth
} from './services/api'

// -----------------------------
// State
// -----------------------------

const question = ref('')
const loading = ref(false)
const mobileMenuOpen = ref(false)

const backendStatus = ref('checking')

const STORAGE_KEY = 'forestguard-conversations'

// -----------------------------
// Backend connection
// -----------------------------

const backendStatusLabel = computed(() => {
  if (backendStatus.value === 'connected') return 'Connected'
  if (backendStatus.value === 'checking') return 'Connecting...'
  return 'Offline'
})

async function verifyBackendConnection() {
  try {
    const health = await checkBackendHealth()

    backendStatus.value =
      health.model_loaded ? 'connected' : 'offline'

  } catch (error) {
    console.error('Backend connection failed:', error)
    backendStatus.value = 'offline'
  }
}

onMounted(() => {
  verifyBackendConnection()
})

// -----------------------------
// Copy answer
// -----------------------------

async function copyMessage(text) {
  try {
    await navigator.clipboard.writeText(text)
    alert('Answer copied successfully!')

  } catch (error) {
    const textarea = document.createElement('textarea')

    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'

    document.body.appendChild(textarea)
    textarea.select()

    const copied = document.execCommand('copy')

    textarea.remove()

    alert(copied ? 'Answer copied!' : 'Could not copy the answer.')
  }
}

// -----------------------------
// Rate answer
// -----------------------------

function rateMessage(messageId, rating) {
  const chat = activeConversation.value

  if (!chat) return

  const message = chat.messages.find(
    item => item.id === messageId
  )

  if (!message || message.role !== 'assistant') return

  message.feedback = message.feedback === rating
    ? null
    : rating
}

// -----------------------------
// Welcome message
// -----------------------------

function welcomeMessage() {
  return {
    id: Date.now() + Math.random(),
    role: 'assistant',
    text: "Hello! I'm ForestGuard. How can I help you with forest-fire prevention and safety?",
    sources: []
  }
}

// -----------------------------
// Initial conversations
// -----------------------------

function createInitialConversations() {
  return [
    {
      id: 1,
      title: 'Forest fire prevention',
      messages: [welcomeMessage()]
    },
    {
      id: 2,
      title: 'Causes of wildfires',
      messages: [welcomeMessage()]
    }
  ]
}

// -----------------------------
// Load conversations
// -----------------------------

function loadConversations() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)

    if (saved) {
      const parsed = JSON.parse(saved)

      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed
      }
    }

  } catch (error) {
    console.error('Could not load conversations:', error)
  }

  return createInitialConversations()
}

const conversations = ref(loadConversations())

const activeConversationId = ref(
  conversations.value[0].id
)

const activeConversation = computed(() => {
  return conversations.value.find(
    chat => chat.id === activeConversationId.value
  ) || null
})

const messages = computed(() => {
  return activeConversation.value?.messages || []
})

// -----------------------------
// Save conversations
// -----------------------------

watch(
  conversations,
  value => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(value)
      )
    } catch (error) {
      console.error('Could not save conversations:', error)
    }
  },
  { deep: true }
)

// -----------------------------
// Suggestions
// -----------------------------

const suggestions = [
  'What are the main causes of forest fires?',
  'How can we prevent wildfires?',
  'What should I do during a forest fire?',
  'How does climate change affect forests?'
]

// -----------------------------
// Select conversation
// -----------------------------

function selectConversation(id) {
  const chat = conversations.value.find(
    item => item.id === id
  )

  if (!chat) return

  activeConversationId.value = id
  question.value = ''
  mobileMenuOpen.value = false

  scrollToBottom()
}

// -----------------------------
// New conversation
// -----------------------------

function newChat() {
  const id = Date.now()

  const chat = {
    id,
    title: 'New conversation',
    messages: [welcomeMessage()]
  }

  conversations.value.unshift(chat)
  activeConversationId.value = id
  question.value = ''

  scrollToBottom()
}

// -----------------------------
// Delete conversation
// -----------------------------

function deleteConversation(id) {
  const index = conversations.value.findIndex(
    chat => chat.id === id
  )

  if (index === -1) return

  conversations.value.splice(index, 1)

  if (activeConversationId.value === id) {
    if (conversations.value.length > 0) {
      activeConversationId.value = conversations.value[0].id
    } else {
      newChat()
    }
  }
}

// -----------------------------
// Scroll
// -----------------------------

async function scrollToBottom() {
  await nextTick()

  document.querySelector('.messages-area')?.scrollTo({
    top: 99999,
    behavior: 'smooth'
  })
}

// -----------------------------
// Send message to real backend
// -----------------------------

async function sendMessage() {
  const text = question.value.trim()

  if (!text || loading.value) return

  const chat = activeConversation.value

  if (!chat) return

  // Add user message immediately.
  chat.messages.push({
    id: Date.now(),
    role: 'user',
    text,
    sources: []
  })

  // Set conversation title.
  if (chat.title === 'New conversation') {
    chat.title = text.length > 25
      ? text.substring(0, 25) + '...'
      : text
  }

  question.value = ''
  loading.value = true

  await scrollToBottom()

  try {
    // Send the question to FastAPI.
    const result = await sendChatMessage(text)

    chat.messages.push({
      id: Date.now() + 1,
      role: 'assistant',
      text: result.answer,
      sources: result.sources || [],
      ragUsed: result.rag_used
    })

    backendStatus.value = 'connected'

  } catch (error) {
    console.error('Chat request failed:', error)

    chat.messages.push({
      id: Date.now() + 2,
      role: 'assistant',
      text: `I couldn't process your question. ${error.message}`,
      sources: [],
      error: true
    })

    // A failed request might be a backend outage.
    await verifyBackendConnection()

  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

// -----------------------------
// Suggestion click
// -----------------------------

function startSuggestion(text) {
  question.value = text
  sendMessage()
}
</script>

<template>
  <div class="min-h-screen bg-[#f5f8f5] text-[#1d3025] flex">

    <!-- Mobile sidebar overlay -->
    <div
      v-if="mobileMenuOpen"
      class="fixed inset-0 z-50 bg-black/60 md:hidden"
      @click="mobileMenuOpen = false"
    >
      <aside
        class="w-72 max-w-[85vw] h-full bg-[#173c2b] text-white flex flex-col p-5 shadow-2xl"
        @click.stop
      >

        <div class="flex items-center justify-between mb-10">
          <div class="flex items-center gap-3">
            <div class="w-11 h-11 bg-[#d5edce] rounded-xl flex items-center justify-center text-2xl">
              🌲
            </div>

            <div>
              <h1 class="font-bold text-xl">ForestGuard</h1>
              <p class="text-xs text-green-200">AI Forest Assistant</p>
            </div>
          </div>

          <button
            @click="mobileMenuOpen = false"
            class="text-2xl text-green-200"
          >
            ×
          </button>
        </div>

        <button
          @click="newChat(); mobileMenuOpen = false"
          class="w-full bg-[#d5edce] text-[#173c2b] py-3 rounded-xl font-semibold mb-8"
        >
          + New conversation
        </button>

        <p class="text-xs uppercase tracking-widest text-green-200 mb-4">
          Recent conversations
        </p>

        <div class="space-y-2 overflow-y-auto flex-1">
          <div
            v-for="chat in conversations"
            :key="chat.id"
            class="flex items-center gap-1"
          >
            <button
              @click="selectConversation(chat.id)"
              class="flex-1 min-w-0 text-left p-3 rounded-lg text-sm truncate"
              :class="activeConversationId === chat.id
                ? 'bg-[#28543d] border border-green-500/30'
                : 'text-green-100 hover:bg-[#28543d]'"
            >
              ◉ {{ chat.title }}
            </button>

            <button
              @click.stop="deleteConversation(chat.id)"
              class="text-green-300 px-2 py-2 hover:text-red-300"
            >
              ×
            </button>
          </div>
        </div>

        <div class="mt-5 border-t border-green-800 pt-5">
          <p class="text-sm font-semibold">ForestGuard AI</p>
          <p class="text-xs text-green-200">Knowledge Assistant</p>
        </div>

      </aside>
    </div>

    <!-- Desktop sidebar -->
    <aside class="hidden md:flex w-72 bg-[#173c2b] text-white flex-col p-5 shrink-0">

      <!-- Logo -->
      <div class="flex items-center gap-3 mb-10">
        <div class="w-11 h-11 bg-[#d5edce] rounded-xl flex items-center justify-center text-2xl">
          🌲
        </div>

        <div>
          <h1 class="font-bold text-xl">ForestGuard</h1>
          <p class="text-xs text-green-200">AI Forest Assistant</p>
        </div>
      </div>

      <!-- New chat -->
      <button
        @click="newChat"
        class="w-full bg-[#d5edce] text-[#173c2b] py-3 rounded-xl font-semibold hover:bg-white transition mb-8"
      >
        + New conversation
      </button>

      <!-- Recent conversations -->
      <div class="flex items-center justify-between mb-4">
        <p class="text-xs uppercase tracking-widest text-green-200">
          Recent conversations
        </p>

        <span class="text-xs text-green-300">
          {{ conversations.length }}
        </span>
      </div>

      <div class="space-y-2 overflow-y-auto flex-1">

        <div
          v-for="chat in conversations"
          :key="chat.id"
          class="flex items-center gap-1 group"
        >
          <button
            @click="selectConversation(chat.id)"
            class="flex-1 min-w-0 text-left p-3 rounded-lg text-sm text-green-100 hover:bg-[#28543d] transition truncate"
            :class="activeConversationId === chat.id
              ? 'bg-[#28543d] border border-green-500/30'
              : ''"
          >
            ◉ {{ chat.title }}
          </button>

          <button
            @click.stop="deleteConversation(chat.id)"
            title="Delete conversation"
            class="text-green-300 hover:text-red-300 px-2 py-2 rounded-lg hover:bg-red-500/10 transition"
          >
            ×
          </button>
        </div>

      </div>

      <!-- Profile -->
      <div class="mt-5 border-t border-green-800 pt-5">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-full bg-[#d5edce] text-[#173c2b] flex items-center justify-center font-bold">
            F
          </div>

          <div>
            <p class="text-sm font-semibold">ForestGuard AI</p>
            <p class="text-xs text-green-200">Knowledge Assistant</p>
          </div>
        </div>
      </div>

    </aside>

    <!-- Main content -->
    <main class="flex-1 flex flex-col min-h-screen min-w-0">

      <!-- Header -->
      <header class="h-20 bg-white border-b border-gray-200 flex items-center gap-3 px-4 md:px-10 shrink-0">

        <!-- Mobile menu button -->
        <button
          type="button"
          @click="mobileMenuOpen = true"
          class="md:hidden flex items-center justify-center w-10 h-10 rounded-lg bg-green-50 text-[#173c2b] text-2xl shrink-0"
          aria-label="Open conversations"
        >
          ☰
        </button>

        <!-- Title -->
        <div class="flex-1 min-w-0">
          <h2 class="font-bold text-lg">ForestGuard AI</h2>
          <p class="text-xs text-gray-500">
            Your forest-fire knowledge assistant
          </p>
        </div>

        <!-- Status -->
        <div class="flex items-center gap-2 bg-green-50 px-3 py-2 rounded-full shrink-0">
          <span
            class="w-2 h-2 rounded-full"
            :class="backendStatus === 'connected'
              ? 'bg-green-500'
              : backendStatus === 'checking'
                ? 'bg-yellow-500'
                : 'bg-red-500'"
          ></span>

          <span class="text-xs font-semibold text-green-700">
            {{ backendStatusLabel }}
          </span>
        </div>

      </header>

      <!-- Chat area -->
      <section class="messages-area flex-1 overflow-y-auto px-4 md:px-10 py-8">

        <div class="max-w-3xl mx-auto">

          <!-- Welcome -->
          <div
            v-if="messages.length === 1"
            class="text-center mb-10"
          >
            <div class="w-16 h-16 bg-[#e0eee1] rounded-2xl flex items-center justify-center text-4xl mx-auto mb-4">
              🌲
            </div>

            <h2 class="text-2xl md:text-3xl font-bold mb-2">
              Protecting forests with AI
            </h2>

            <p class="text-gray-500 text-sm">
              Ask questions and explore forest-fire knowledge.
            </p>
          </div>

          <!-- Messages -->
          <div
            v-for="message in messages"
            :key="message.id"
            class="flex gap-3 mb-7"
            :class="message.role === 'user' ? 'flex-row-reverse' : ''"
          >

            <!-- Avatar -->
            <div
              class="w-9 h-9 shrink-0 rounded-xl flex items-center justify-center"
              :class="message.role === 'assistant'
                ? 'bg-[#173c2b] text-white'
                : 'bg-[#dcebdc]'"
            >
              {{ message.role === 'assistant' ? '🌲' : '👤' }}
            </div>

            <div class="max-w-[85%] min-w-0">

              <!-- Sender -->
              <p class="text-xs font-bold mb-2 text-gray-500">
                {{ message.role === 'assistant' ? 'ForestGuard' : 'You' }}
              </p>

              <!-- Message text -->
              <div
                class="p-4 rounded-2xl text-sm leading-7 whitespace-pre-wrap break-words"
                :class="message.role === 'assistant'
                  ? 'bg-white border border-gray-200'
                  : 'bg-[#e0eee1]'"
              >
                {{ message.text }}
              </div>

              <!-- Copy and feedback buttons -->
              <div
                v-if="message.role === 'assistant'"
                class="flex items-center flex-wrap gap-2 mt-2"
              >

                <button
                  @click="copyMessage(message.text)"
                  class="text-xs text-gray-500 hover:text-green-700 px-3 py-1.5 rounded-lg hover:bg-green-50 transition"
                >
                  📋 Copy answer
                </button>

                <span class="text-xs text-gray-400">
                  Helpful?
                </span>

                <button
                  @click="rateMessage(message.id, 'positive')"
                  :class="message.feedback === 'positive'
                    ? 'bg-green-100 text-green-800 border-green-300'
                    : 'bg-white text-gray-500 border-gray-200'"
                  class="border rounded-lg px-3 py-1 text-xs hover:bg-green-50 transition"
                  aria-label="Good answer"
                >
                  👍
                </button>

                <button
                  @click="rateMessage(message.id, 'negative')"
                  :class="message.feedback === 'negative'
                    ? 'bg-red-100 text-red-800 border-red-300'
                    : 'bg-white text-gray-500 border-gray-200'"
                  class="border rounded-lg px-3 py-1 text-xs hover:bg-red-50 transition"
                  aria-label="Bad answer"
                >
                  👎
                </button>

              </div>

              <!-- Sources -->
              <div
                v-if="message.sources && message.sources.length"
                class="mt-3"
              >
                <p class="text-xs font-bold text-gray-500 mb-2">
                  📚 Sources
                </p>

                <div
                  v-for="(source, index) in message.sources"
                  :key="index"
                  class="bg-white border border-gray-200 rounded-xl p-3 mb-2 text-xs"
                >
                  <p class="font-semibold text-[#28543d]">
                    {{ source.title }}
                  </p>

                  <p class="text-gray-500 mt-1">
                    Page {{ source.page }}
                  </p>
                </div>
              </div>

            </div>
          </div>

          <!-- Typing indicator -->
          <div v-if="loading" class="flex gap-3 mb-6">

            <div class="w-9 h-9 shrink-0 bg-[#173c2b] text-white rounded-xl flex items-center justify-center">
              🌲
            </div>

            <div class="bg-white border border-gray-200 rounded-xl px-5 py-3 text-sm text-gray-500">
              ForestGuard is thinking...
              <span class="animate-pulse">● ● ●</span>
            </div>

          </div>

          <!-- Suggestions -->
          <div
            v-if="messages.length === 1"
            class="mt-10"
          >

            <p class="text-sm font-semibold mb-4 text-gray-600">
              Try asking
            </p>

            <div class="grid sm:grid-cols-2 gap-3">

              <button
                v-for="item in suggestions"
                :key="item"
                @click="startSuggestion(item)"
                class="text-left bg-white border border-gray-200 rounded-xl p-4 text-sm hover:border-green-600 hover:bg-green-50 transition"
              >
                {{ item }}
                <span class="block text-green-700 mt-2">↗</span>
              </button>

            </div>
          </div>

        </div>
      </section>

      <!-- Input -->
      <footer class="bg-white border-t border-gray-200 px-4 md:px-10 py-5 shrink-0">

        <form
          @submit.prevent="sendMessage"
          class="max-w-3xl mx-auto"
        >

          <div class="flex items-center gap-3 border border-gray-300 rounded-2xl p-2 focus-within:border-green-700 shadow-sm">

            <input
              v-model="question"
              type="text"
              placeholder="Ask ForestGuard something..."
              class="flex-1 min-w-0 px-3 py-3 outline-none text-sm"
              :disabled="loading"
            />

            <button
              type="submit"
              :disabled="!question.trim() || loading"
              class="bg-[#173c2b] text-white px-5 py-3 rounded-xl hover:bg-[#28543d] disabled:opacity-40 transition"
            >
              Send ↑
            </button>

          </div>

          <p class="text-center text-xs text-gray-400 mt-3">
            ForestGuard AI can make mistakes. Always follow official safety guidance.
          </p>

        </form>

      </footer>

    </main>
  </div>
</template>


<style>
:root {
  font-family: Inter, "Segoe UI", sans-serif;
  color: #1f2937;
  background: #f5f7f6;
}

body {
  margin: 0;
  background: #f5f7f6;
}

main {
  background: #f5f7f6;
}

.messages-area {
  background: #f5f7f6 !important;
  color: #1f2937;
}

/* Assistant message */
.messages-area .whitespace-pre-wrap:not(.bg-\[\#e0eee1\]) {
  background: #ffffff !important;
  color: #263b35 !important;
  border: 1px solid #e1e8e5 !important;
  border-radius: 18px !important;
  box-shadow: 0 3px 12px rgba(20, 50, 40, 0.05);
}

/* User message */
.messages-area .bg-\[\#e0eee1\] {
  background: #dcefe8 !important;
  color: #194b3e !important;
  border: 1px solid #c6e3d8 !important;
  border-radius: 18px !important;
}

/* Sidebar */
aside.bg-\[\#173c2b\] {
  background: #173f35 !important;
}

/* Header */
main header {
  background: #ffffff !important;
  border-bottom: 1px solid #e3eae6 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

main header h2 {
  color: #173f35 !important;
}

/* Source cards */
.messages-area .rounded-xl.bg-white {
  background: #ffffff !important;
  border: 1px solid #e1e8e5 !important;
}

/* Suggestion cards */
.messages-area button.bg-white {
  background: #ffffff !important;
  color: #263b35 !important;
  border: 1px solid #e1e8e5 !important;
  border-radius: 14px !important;
}

.messages-area button.bg-white:hover {
  background: #edf7f2 !important;
  border-color: #80b9a2 !important;
}

/* Input */
footer {
  background: #ffffff !important;
  border-top: 1px solid #e1e8e5 !important;
}

footer form > div {
  background: #ffffff !important;
  border: 1px solid #ccd9d3 !important;
  border-radius: 16px !important;
  box-shadow: 0 3px 12px rgba(20, 50, 40, 0.05);
}

footer form > div:focus-within {
  border-color: #16836f !important;
  box-shadow: 0 0 0 3px rgba(22, 131, 111, 0.12);
}

/* Send button */
footer button[type="submit"] {
  background: #176b57 !important;
  color: white !important;
  border-radius: 12px !important;
}

footer button[type="submit"]:hover {
  background: #105441 !important;
}

/* General buttons */
button {
  transition: background 0.2s ease, border-color 0.2s ease;
}

button:focus-visible,
input:focus-visible {
  outline: 3px solid rgba(22, 131, 111, 0.25);
  outline-offset: 2px;
}

/* Mobile */
@media (max-width: 767px) {
  .messages-area {
    padding: 20px 14px !important;
  }

  .messages-area .whitespace-pre-wrap {
    font-size: 14px;
  }
}
</style>
