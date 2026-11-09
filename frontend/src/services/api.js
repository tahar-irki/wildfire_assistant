const API_BASE_URL = (
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
).replace(/\/+$/, '')

export async function sendChatMessage(question) {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ question })
  })

  let data

  try {
    data = await response.json()
  } catch {
    throw new Error('The backend returned an invalid response.')
  }

  if (!response.ok) {
    throw new Error(
      data.detail || `Backend request failed (${response.status}).`
    )
  }

  return data
}

export async function checkBackendHealth() {
  const response = await fetch(`${API_BASE_URL}/health`)

  if (!response.ok) {
    throw new Error('Backend health check failed.')
  }

  return response.json()
}