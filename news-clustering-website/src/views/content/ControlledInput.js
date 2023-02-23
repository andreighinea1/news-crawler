import { Input } from 'components/ui'

const ControlledInput = (props) => {

    const { size, value, setValue, onClick, disabled } = props

    const handleChange = (e) => setValue(e.target.value);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            onClick(e);
        }
    }

    return (
        <div>
            <Input
                value={value}
                onChange={handleChange}
                placeholder="Enter a URL to a news website"
                size={size}
                onKeyDown={handleKeyDown}
                disabled={disabled}
            />
        </div>
    )
}

export default ControlledInput