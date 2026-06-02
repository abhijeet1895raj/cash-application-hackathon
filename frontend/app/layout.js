export const metadata = {
  title: 'Cash Application Foundry',
  description: '5-agent AI pipeline for bank reconciliation',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="bg-gray-50">
        {children}
      </body>
    </html>
  )
}
