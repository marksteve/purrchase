/** @jsx React.DOM */

var React = require('react/addons');

var Button = React.createClass({
  showForm: function() {
    this.props.form.setState({hidden: false});
  },
  render: function() {
    return (
      <button
        className="payload-button"
        onClick={this.showForm}
        >
        Pay with Globe Load
      </button>
    );
  }
});

var Form = React.createClass({
  getInitialState: function() {
    return {
      hidden: true
    };
  },
  hide: function() {
    this.setState({hidden: true});
  },
  render: function() {
    var className = React.addons.classSet({
      'payload-form': true,
      'hidden': this.state.hidden
    });
    var options = this.props.options;
    return (
      <div className={className}>
        <div
          className="overlay"
          onClick={this.hide}
        />
        <div
          className="box"
          >
          <h2>{options.header}</h2>
          <p className="details">
            {options.desc} ({options.amount})
          </p>
          <p>
            <input ref="number" type="text" placeholder="Cellphone #" />
          </p>
          <p>
            <button
              >
              Pay with Globe Load
            </button>
          </p>
        </div>
      </div>
    );
  }
});


window.payload = function(options) {

  var container = document.createElement('div');
  document.body.appendChild(container);

  var form = React.renderComponent(
    <Form options={options} />,
    container
  );

  React.renderComponent(
    <Button form={form} />,
    document.getElementById('payload')
  );

}
