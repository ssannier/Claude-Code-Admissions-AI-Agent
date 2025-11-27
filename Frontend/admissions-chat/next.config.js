/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001',
    NEXT_PUBLIC_AGENT_PROXY_URL: process.env.NEXT_PUBLIC_AGENT_PROXY_URL || 'http://localhost:3002'
  }
}

module.exports = nextConfig
