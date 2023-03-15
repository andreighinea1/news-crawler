import React, {useEffect, useState} from 'react'
import {useLocation} from 'react-router-dom';
import {DataTable} from "../../components/shared";
import paginate from "../../utils/paginate";
import dateToString from "../../utils/dateToString";
import sortBy from "../../utils/sortBy";

const getSimilarNewsBaseUrl = 'http://localhost:8000/news-clustering/get-similar-news'

const NewsQueryResult = () => {
    const location = useLocation();
    const [data, setData] = useState([])
    const [loading, setLoading] = useState(false)
    const [tableData, setTableData] = useState(
        {
            total: 0,
            pageIndex: 1,
            pageSize: 10,
            query: '',
            sort: {
                order: '',
                key: ''
            }
        }
    )

    const columns = [
        {
            Header: 'URL',
            accessor: 'url',
            sortable: true,
        },
        {
            Header: 'Author',
            accessor: 'author',
            sortable: true,
        },
        {
            Header: 'Publish Time',
            accessor: 'publishedAt',
            sortable: true,
        },
    ]

    const handlePaginationChange = pageIndex => {
        setTableData(prevData => ({...prevData, ...{pageIndex}}))
    }

    const handleSelectChange = pageSize => {
        setTableData(prevData => ({...prevData, ...{pageSize}}))
    }

    const handleSort = ({order, key}, aaa) => {
        // console.log({order, key})
        // console.log(aaa)
        setTableData(prevData => ({...prevData, ...{sort: {order, key}}}))
    }

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);

            const url = location.state.url;
            const title = location.state.title;
            const content = location.state.content;

            let similarNews = [];
            fetch(new Request(getSimilarNewsBaseUrl), {
                method: "POST",
                body: JSON.stringify({
                    url: url,
                    title: title,
                    content: content,
                    urls: null,
                }),
                headers: {
                    "Content-Type": "application/json"
                }
            })
                .then(response2 => response2.json())
                .then(res2 => {
                    if (res2 && res2.similar_news.length > 0) {
                        similarNews = [...res2.similar_news];

                        similarNews.forEach(article => {
                            // Used for sorting
                            article.dateSortId = Date.parse(article.publishedAt)

                            // Parse date to be more human-readable
                            const newDate = dateToString(new Date(article.publishedAt));
                            if (newDate !== "NaN-NaN-NaN, Invalid Date") {
                                article.publishedAt = newDate;
                            }
                        })
                        if (tableData.sort.key !== '' && tableData.sort.order !== '') {
                            similarNews.sort(sortBy(
                                tableData.sort.key,
                                tableData.sort.order === 'desc',
                                null,
                                false)
                            )
                        }

                        setData(paginate(
                            similarNews,
                            tableData.pageSize,
                            tableData.pageIndex)
                        );
                    }

                    setLoading(false);
                    setTableData(prevData => ({...prevData, ...{total: similarNews.length}}));
                });
        }
        fetchData();
    }, [tableData.pageIndex, tableData.sort, tableData.pageSize, tableData.query])

    return (
        <DataTable
            columns={columns}
            data={data}
            loading={loading}
            pagingData={tableData}
            onPaginationChange={handlePaginationChange}
            onSelectChange={handleSelectChange}
            onSort={handleSort}
        />
    )
}

export default NewsQueryResult