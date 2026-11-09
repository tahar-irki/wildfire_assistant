
const API_URL = import.meta.env.VITE_API_URL

export async function sendMessageToBot(question) {
  if (!API_URL) {
    throw new Error('Backend API URL is not configured')
  }

  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ question })
  })

  if (!response.ok) {
    throw new Error(`Server error: ${response.status}`)
  }

  return await response.json()
}