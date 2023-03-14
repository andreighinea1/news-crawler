import React from 'react'
import authRoute from './authRoute'

export const publicRoutes = [
    ...authRoute
]

export const protectedRoutes = [
    {
        key: 'searchNewsByTitle',
        path: '/search-menu-news-by-title',
        component: React.lazy(() => import('views/content/SearchNewsByTitle')),
        authority: [],
    },
    {
        key: 'newsQueryHistory',
        path: '/search-menu-news-query-history',
        component: React.lazy(() => import('views/content/NewsQueryHistory')),
        authority: [],
    },
    {
        key: 'newsQueryResult',
        path: '/news-query-result',
        component: React.lazy(() => import('views/content/NewsQueryResult')),
        authority: [],
    },
]