import React, {useEffect, useState} from 'react'
import {useLocation, useNavigate} from 'react-router-dom';
import {DataTable} from "../../components/shared";
import paginate from "../../utils/paginate";
import dateToString from "../../utils/dateToString";
import sortBy from "../../utils/sortBy";
import {Button} from 'components/ui'

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
    let navigate = useNavigate();

    const handleSimilarNews = (cellProps) => {
        navigate("/similar-news-result", {
            replace: true,
            state: {
                title: cellProps.cell.value.title,
                content: cellProps.cell.value.content,
                url: cellProps.cell.value.url,
            }
        });
    }

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
        {
            Header: '',
            id: 'similarity',
            accessor: (row) => row,
            Cell: props => <Button size="xs" onClick={() => handleSimilarNews(props)}>See Similar News</Button>
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

            const searchedArticles = [...location.state.searchedArticles]
            searchedArticles.forEach(article => {
                // Used for sorting
                article.dateSortId = Date.parse(article.publishedAt)

                // Parse date to be more human-readable
                const newDate = dateToString(new Date(article.publishedAt));
                if (newDate !== "NaN-NaN-NaN, Invalid Date") {
                    article.publishedAt = newDate;
                }
            })
            if (tableData.sort.key !== '' && tableData.sort.order !== '') {
                searchedArticles.sort(sortBy(
                    tableData.sort.key,
                    tableData.sort.order === 'desc',
                    null,
                    false)
                )
            }

            setData(paginate(
                searchedArticles,
                tableData.pageSize,
                tableData.pageIndex)
            );
            setLoading(false);
            setTableData(prevData => ({...prevData, ...{total: searchedArticles.length}}))
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